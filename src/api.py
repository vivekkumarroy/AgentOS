from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
from .config import settings, setup_logging
from .tools.registry import ToolRegistry
from .tools.filesystem import ReadFileTool, WriteFileTool, ListDirectoryTool, SearchFilesTool
from .tools.python_exec import PythonExecutionTool
from .tools.web import WebSearchTool, WebExtractTool
from .tools.memory_tools import MemoryStoreTool, MemorySearchTool, MemoryDeleteTool
from .execution.executor import Executor
from .models.state import ToolCall, Observation, Task
from .verification.verifier import VerificationEngine
from .recovery.diagnosis import FailureDiagnosisEngine
from .recovery.replanner import RecoveryPlanner
from .recovery.circuit_breaker import CircuitBreaker
from .llm.client import LLMClient
from .planning.planner import Planner
from .memory.memory import ShortTermMemory
from .memory.long_term import ChromaVectorStore, LongTermMemory
from .memory.embeddings import get_embedding_provider
from .rag.pipeline import RAGPipeline
from .orchestration.orchestrator import Orchestrator

setup_logging()

app = FastAPI(title="AgentOS API", version="0.1.0")
app_is_ready = True  # Used by /ready to determine if initialization succeeded

# Setup Phase 4 components
embedding_provider = get_embedding_provider()
vector_store = ChromaVectorStore(
    db_path=settings.vector_db_path,
    collection_name=settings.vector_collection_name,
    embedding_function=embedding_provider
)
long_term_memory = LongTermMemory(vector_store)
rag_pipeline = RAGPipeline(
    vector_store=vector_store,
    workspace=settings.agent_workspace,
    chunk_size=settings.rag_chunk_size,
    chunk_overlap=settings.rag_chunk_overlap
)

# Setup global registry
registry = ToolRegistry()
registry.register(ReadFileTool())
registry.register(WriteFileTool())
registry.register(ListDirectoryTool())
registry.register(SearchFilesTool())
registry.register(PythonExecutionTool())
registry.register(WebSearchTool())
registry.register(WebExtractTool())

# Register Phase 4 Memory Tools
registry.register(MemoryStoreTool(long_term_memory))
registry.register(MemorySearchTool(long_term_memory))
registry.register(MemoryDeleteTool(long_term_memory))

executor = Executor(registry)
llm_client = LLMClient()
planner = Planner(llm_client)
verifier = VerificationEngine(llm_client)
diagnoser = FailureDiagnosisEngine(llm_client)
replanner = RecoveryPlanner(llm_client)
circuit_breaker = CircuitBreaker()

from .evaluation.framework import Evaluator
from .evaluation.models import TestCase, EvalReport
from .tracing.tracer import LocalTracer

# Setup Phase 5 components
tracer = LocalTracer(settings.trace_storage_path)

evaluator = Evaluator(
    planner=planner,
    executor=executor,
    verifier=verifier,
    diagnoser=diagnoser,
    replanner=replanner,
    circuit_breaker=circuit_breaker,
    tracer=tracer
)

# Setup Phase 6 Multi-Agent components
from .models.agent import AgentProfile
from .orchestration.registry import AgentRegistry
from .orchestration.factory import SubAgentFactory
from .tools.delegation import DelegateTaskTool

agent_registry = AgentRegistry()
agent_registry.register(AgentProfile(
    name="Coordinator",
    description="Main orchestration agent capable of planning and delegation.",
    system_prompt="You are the primary coordinator agent.",
    allowed_tools=registry.list_tools() + ["delegate_task"]
))
agent_registry.register(AgentProfile(
    name="Calculator",
    description="Specialized agent for mathematical and logic calculations via Python.",
    system_prompt="You are a strict calculation agent. Use python to solve math problems.",
    allowed_tools=["python_exec"]
))

subagent_factory = SubAgentFactory(registry, llm_client, tracer)
registry.register(DelegateTaskTool(agent_registry, subagent_factory))



class ExecuteTaskRequest(BaseModel):
    task: Task

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logging.getLogger(__name__).error(f"Unhandled API error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "message": str(exc)}
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def ready_check():
    if app_is_ready:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "not_ready"})

@app.get("/tools")
def list_tools():
    return {"tools": registry.get_all_schemas()}

@app.post("/tools/execute")
def execute_tool(tool_call: ToolCall) -> Observation:
    return executor.execute_tool(tool_call)

@app.post("/tasks/execute")
def execute_task_endpoint(request: ExecuteTaskRequest) -> Task:
    memory = ShortTermMemory()
    memory.get_state().tasks_state[request.task.task_id] = request.task
    
    orch = Orchestrator(
        planner=planner,
        memory=memory,
        executor=executor,
        verifier=verifier,
        diagnoser=diagnoser,
        replanner=replanner,
        circuit_breaker=circuit_breaker,
        tracer=tracer
    )
    
    return orch.run_task_with_recovery(request.task.task_id)

# Phase 4 Endpoints
class MemoryStoreRequest(BaseModel):
    text: str
    metadata: Dict[str, Any] = {}

@app.post("/memory/store")
def store_memory(request: MemoryStoreRequest):
    record = long_term_memory.store_memory(request.text, request.metadata)
    return {"status": "success", "memory_id": record.memory_id}

class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/memory/search")
def search_memory(request: MemorySearchRequest):
    results = long_term_memory.retrieve_memories(request.query, request.top_k)
    return {"results": results}

class MemoryDeleteRequest(BaseModel):
    memory_id: str

@app.post("/memory/delete")
def delete_memory(request: MemoryDeleteRequest):
    long_term_memory.delete_memory(request.memory_id)
    return {"status": "success", "memory_id": request.memory_id}

@app.get("/memory/count")
def count_memory():
    return {"count": long_term_memory.count_memories()}

class RAGIngestRequest(BaseModel):
    file_path: str

@app.post("/rag/ingest")
def rag_ingest(request: RAGIngestRequest):
    try:
        chunks = rag_pipeline.ingest_document(request.file_path)
        return {"status": "success", "chunks_stored": chunks}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rag/search")
def rag_search(request: MemorySearchRequest):
    results = rag_pipeline.retrieve(request.query, request.top_k)
    return {"results": results}

# Phase 5 Endpoints
@app.get("/traces/{task_id}")
def get_traces(task_id: str):
    return {"traces": tracer.get_traces(task_id)}

class EvaluateRequest(BaseModel):
    cases: List[TestCase]

@app.post("/evaluate")
def evaluate(request: EvaluateRequest):
    report = evaluator.evaluate(request.cases)
    return report

# Phase 6 Endpoints
@app.get("/agents")
def get_agents():
    return {"agents": [p.model_dump() for p in agent_registry.list()]}


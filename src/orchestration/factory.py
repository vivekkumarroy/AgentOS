from .orchestrator import Orchestrator
from ..models.agent import AgentProfile
from ..tools.registry import ToolRegistry
from ..llm.client import LLMClient
from ..planning.planner import Planner
from ..memory.memory import ShortTermMemory
from ..execution.executor import Executor
from ..verification.verifier import VerificationEngine
from ..recovery.diagnosis import FailureDiagnosisEngine
from ..recovery.replanner import RecoveryPlanner
from ..recovery.circuit_breaker import CircuitBreaker
from ..tracing.tracer import Tracer
from ..tracing.events import TraceEvent
from typing import List

class SubAgentTracerProxy(Tracer):
    def __init__(self, parent_tracer: Tracer, parent_run_id: str, subagent_name: str, delegation_depth: int):
        self.parent_tracer = parent_tracer
        self.parent_run_id = parent_run_id
        self.subagent_name = subagent_name
        self.delegation_depth = delegation_depth

    def emit(self, event: TraceEvent):
        event.parent_run_id = self.parent_run_id
        event.subagent_name = self.subagent_name
        event.delegation_depth = self.delegation_depth
        if self.parent_tracer:
            self.parent_tracer.emit(event)

    def get_traces(self, task_id: str) -> List[TraceEvent]:
        if self.parent_tracer:
            return self.parent_tracer.get_traces(task_id)
        return []

class SubAgentFactory:
    def __init__(self, global_registry: ToolRegistry, llm_client: LLMClient, tracer: Tracer = None):
        self.global_registry = global_registry
        self.llm_client = llm_client
        self.tracer = tracer
        
    def create_worker(self, profile: AgentProfile, parent_run_id: str, delegation_depth: int) -> Orchestrator:
        """Create a new, isolated Orchestrator for the sub-agent."""
        
        # 1. Filter tools to only those allowed
        worker_registry = ToolRegistry()
        for tool_name in profile.allowed_tools:
            tool = self.global_registry.get(tool_name)
            if tool:
                worker_registry.register(tool)
            else:
                raise ValueError(f"Tool '{tool_name}' allowed by profile '{profile.name}' is not found in global registry.")
                
        # 2. Isolated memory
        worker_memory = ShortTermMemory()
        
        # We need to ensure the parent_run_id and subagent_name are added to the execution context
        # so tracing can correlate them.
        worker_memory.get_state().execution_context["run_id"] = parent_run_id
        worker_memory.get_state().execution_context["subagent_name"] = profile.name
        worker_memory.get_state().execution_context["delegation_depth"] = delegation_depth

        # 3. Create a tracer proxy that injects the correlation fields
        worker_tracer = SubAgentTracerProxy(self.tracer, parent_run_id, profile.name, delegation_depth)

        # 4. Dedicated components
        worker_planner = Planner(self.llm_client)
        worker_executor = Executor(worker_registry)
        worker_verifier = VerificationEngine(self.llm_client)
        worker_diagnoser = FailureDiagnosisEngine(self.llm_client)
        worker_replanner = RecoveryPlanner(self.llm_client)
        worker_circuit_breaker = CircuitBreaker()
        
        # 5. Construct Orchestrator
        worker_orchestrator = Orchestrator(
            planner=worker_planner,
            memory=worker_memory,
            executor=worker_executor,
            verifier=worker_verifier,
            diagnoser=worker_diagnoser,
            replanner=worker_replanner,
            circuit_breaker=worker_circuit_breaker,
            tracer=worker_tracer
        )
        
        return worker_orchestrator

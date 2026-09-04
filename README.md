# AgentOS

AgentOS is an autonomous AI task-solving platform designed for production environments. It provides orchestration, multi-step planning, tool usage, failure recovery, and state management.

## Architecture and Capabilities
1. Phase 1: Core Foundation & Scaffolding (State, Orchestrator, LLM Client)
2. Phase 2: Tooling & Execution Engine (Filesystem, Python Execution, Web Search)
3. Phase 3: Verification, Failure Diagnosis & Recovery (Autonomous Loops)
4. Phase 4: Long-Term Memory & RAG (Persistent ChromaDB, Document Ingestion)

### Core Execution Flow
```
USER GOAL -> ORCHESTRATOR -> PLANNER -> TASK -> EXECUTOR -> VERIFIER
                                                               |
    +----------------------------------------------------------+
    |
SUCCESS? --(YES)--> COMPLETED
    |
  (NO)
    v
FAILURE DIAGNOSIS -> RECOVERY PLANNER -> EXECUTOR (Retry loop with Circuit Breaker)
```

### Components
- **Tool Registry:** Manages tools and exposes Pydantic schemas to LLMs.
- **Verification Engine:** Validates that the executed tool actually fulfilled the expected goal.
- **Failure Diagnosis:** Diagnoses why a task failed and if it is recoverable.
- **Recovery Replanning:** Modifies the task plan to avoid repeating the same failure.
- **Circuit Breaker:** Tracks action history and terminates loops when the exact same failed action is repeated.
- **Available Tools:**
  - `read_file`, `write_file`, `list_directory`, `search_files`: Restricted securely to `AGENT_WORKSPACE`.
  - `python_exec`: Executes Python code inside a subprocess. *WARNING: This is NOT a secure sandbox.*
  - `web_search`, `web_extract`: Safely searches and extracts readable web content.

## Project Structure
```
AgentOS/
├── src/
│   ├── api.py            # API entry point & tool execution endpoints
│   ├── config.py         # Application configuration
│   ├── execution/        # Tool execution pipeline
│   ├── llm/              # LLM client & structured outputs
│   ├── memory/           # Agent execution state storage
│   ├── models/           # Pydantic schemas
│   ├── orchestration/    # Dependency tracking and loop coordination
│   ├── planning/         # Task decomposition logic
│   ├── recovery/         # Diagnosis, Circuit Breaking & Replanning
│   ├── tools/            # Tool implementations & registry
│   └── verification/     # Observation verification engine
├── tests/                # Comprehensive test suite (Phases 1-3)
├── .env.example          # Config template
├── main.py               # Main startup script
└── requirements.txt      # Dependencies
```

## Installation
Ensure you have Python 3.11+ installed.
```bash
pip install -r requirements.txt
```

## Environment Configuration
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```
Key configurations include:
- `LLM_PROVIDER`: The LLM provider (e.g., `openai`, `anthropic`, `gemini`)
- `LLM_MODEL`: The specific model to use (e.g., `gpt-4o-mini`)
- `API_KEY`: Your secret LLM API key
- `AGENT_WORKSPACE`: Secure workspace directory for file tools (e.g., `./workspace`)
- `PYTHON_EXEC_TIMEOUT`: Timeout in seconds for python execution tools
- `SEARCH_API_KEY`: API key for web search tools
- `MAX_TASK_RETRIES`: Maximum allowed retries in recovery loop (default: 3)

## Running the Application
Start the AgentOS API server:
```bash
python main.py
```
Check health: `http://localhost:8000/health`
List registered tools: `http://localhost:8000/tools`

## Running Tests
Run the entire test suite using Pytest (ensuring backward compatibility):
```bash
pytest -v -W default
```

## Example API Execution
Execute a tool directly via the API:
```bash
curl -X POST http://localhost:8000/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool_name": "write_file", "arguments": {"path": "test.txt", "content": "Hello World"}}'
```

Execute a complete autonomous recovery loop for a Task:
```bash
curl -X POST http://localhost:8000/tasks/execute \
     -H "Content-Type: application/json" \
     -d '{"task": {"task_id": "t1", "description": "Write a test file", "dependencies": [], "required_tools": ["write_file"], "expected_output": "File written"}}'
```


# AgentOS - System Architecture

## 1. Design Principles
- **Modularity:** The system is heavily decoupled. Planning, Memory, Tools, and Orchestration are distinct modules.
- **Extensibility:** New tools, LLM providers, and memory stores can be plugged in with minimal friction.
- **Resiliency:** The system assumes LLMs hallucinate and tools fail. Verification and recovery are first-class citizens.

## 2. Component Breakdown

### 2.1 API / Interface Layer
- **Role:** Entry point for user interactions.
- **Responsibilities:** Ingests user goals, streams execution traces back to the client, and returns human-readable final answers.

### 2.2 Orchestrator
- **Role:** The central nervous system.
- **Responsibilities:** Manages the main execution loop. It passes state between the Planner, Executor, and Verification engine. It acts as the ultimate authority on state transitions (e.g., from `EXECUTING` to `REPLANNING`).

### 2.3 Planner
- **Role:** The strategist.
- **Responsibilities:** Takes a high-level goal and generates a Directed Acyclic Graph (DAG) or sequential list of tasks. When notified of a failure by the Orchestrator, it generates an updated recovery plan.

### 2.4 Executor
- **Role:** The actor.
- **Responsibilities:** Maps tasks to specific tool calls, executes them securely, and gathers observations. 

### 2.5 Tool Registry
- **Role:** The capabilities repository.
- **Responsibilities:** Stores available tools (Web Retrieval, File Processing, Code Execution, Data Analysis) and their JSON schemas for LLM consumption.

### 2.6 Memory Manager
- **Short-Term Memory:** Maintains the immediate conversation context and observation history (scratchpad) within the current session.
- **Long-Term Memory:** Interfaces with a Vector Database to store past learnings, user preferences, and indexed documents for Retrieval-Augmented Generation (RAG).

### 2.7 Verification & Diagnostics Engine
- **Role:** The auditor.
- **Responsibilities:** Assesses the observation output from the Executor against the intended goal of the task. If it detects a failure, it generates a Failure Diagnosis report to be sent back to the Planner for recovery.

## 3. Proposed Technology Stack
- **Language:** Python 3.11+
- **LLM Interface:** Litellm (for provider-agnostic LLM calls) or direct OpenAI/Anthropic/Gemini SDKs.
- **Data Models:** Pydantic (for strict type checking, tool schema generation, and structured LLM outputs).
- **Long-Term Memory:** ChromaDB or Qdrant.
- **Code Execution:** Docker-based sandbox or isolated sub-processes.
- **Web Retrieval:** Playwright (for dynamic rendering) and BeautifulSoup.
- **Tracing / Logging:** LangSmith or custom structured logging.

## 4. Identified Risks
- **Infinite Loops:** The recovery/replan cycle can loop endlessly if an LLM is stuck. (Mitigation: Implement strict retry budgets/circuit breakers).
- **Security:** Autonomous code execution is highly dangerous. (Mitigation: strictly sandbox execution environments).
- **Context Window Exhaustion:** Long-running tasks will fill up the context window. (Mitigation: implement intelligent context summarization in the Memory Manager).

## 5. Required Environment Variables
- LLM Provider Keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`)
- Web Search APIs (e.g., `TAVILY_API_KEY` or `SERPER_API_KEY`)
- Tracing tools (e.g., `LANGCHAIN_API_KEY` if using LangSmith)

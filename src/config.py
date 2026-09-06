import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    api_key: str = ""
    timeout: int = 60
    app_env: str = "development"
    
    agent_workspace: str = "./workspace"
    python_exec_timeout: int = 10
    python_max_output: int = 10000
    search_api_key: str = ""
    max_task_retries: int = 3
    
    # Phase 4
    vector_db_path: str = "./data/chroma"
    vector_collection_name: str = "agent_long_term_memory"
    embedding_model: str = "local"
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    
    # Tracing
    trace_storage_path: str = "traces.jsonl"
    
    # Phase 6: Multi-Agent
    max_delegation_depth: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

def setup_logging():
    level = logging.DEBUG if settings.app_env.lower() == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

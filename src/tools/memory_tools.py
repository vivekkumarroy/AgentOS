from typing import Dict, Any, Type
import logging
from pydantic import BaseModel, Field
from .registry import BaseTool
from ..memory.long_term import LongTermMemory

logger = logging.getLogger(__name__)

class MemoryStoreArgs(BaseModel):
    text: str = Field(..., description="The text information to store in long-term memory.")

class MemoryStoreTool(BaseTool):
    name = "memory_store"
    description = "Stores important information in persistent long-term memory."
    args_schema: Type[BaseModel] = MemoryStoreArgs
    
    def __init__(self, memory: LongTermMemory):
        self.memory = memory

    def execute(self, args: Dict[str, Any]) -> str:
        text = args.get("text")
        record = self.memory.store_memory(text)
        return f"Stored memory successfully with id: {record.memory_id}"

class MemorySearchArgs(BaseModel):
    query: str = Field(..., description="The query to search for in long-term memory.")
    top_k: int = Field(5, description="Number of results to return.")

class MemorySearchTool(BaseTool):
    name = "memory_search"
    description = "Searches persistent long-term memory for relevant information."
    args_schema: Type[BaseModel] = MemorySearchArgs
    
    def __init__(self, memory: LongTermMemory):
        self.memory = memory

    def execute(self, args: Dict[str, Any]) -> str:
        query = args.get("query")
        top_k = args.get("top_k", 5)
        
        # Security: validate top_k
        if not isinstance(top_k, int) or top_k <= 0 or top_k > 50:
            top_k = 5
            
        results = self.memory.retrieve_memories(query, top_k)
        if not results:
            return "No relevant memories found."
            
        formatted_results = []
        for i, r in enumerate(results):
            formatted_results.append(f"Result {i+1} (ID: {r['id']}):\n{r['text']}")
            
        return "\n\n".join(formatted_results)

class MemoryDeleteArgs(BaseModel):
    memory_id: str = Field(..., description="The ID of the memory to delete.")

class MemoryDeleteTool(BaseTool):
    name = "memory_delete"
    description = "Deletes a specific entry from long-term memory."
    args_schema: Type[BaseModel] = MemoryDeleteArgs
    
    def __init__(self, memory: LongTermMemory):
        self.memory = memory

    def execute(self, args: Dict[str, Any]) -> str:
        memory_id = args.get("memory_id")
        self.memory.delete_memory(memory_id)
        return f"Deleted memory with id: {memory_id}"

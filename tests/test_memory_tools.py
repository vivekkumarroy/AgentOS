import tempfile
import pytest
from src.memory.long_term import ChromaVectorStore, LongTermMemory
from src.tools.memory_tools import MemoryStoreTool, MemorySearchTool, MemoryDeleteTool

@pytest.fixture
def memory():
    tmpdir = tempfile.mkdtemp()
    store = ChromaVectorStore(tmpdir, "test_col")
    yield LongTermMemory(store)

def test_memory_tools(memory):
    store_tool = MemoryStoreTool(memory)
    search_tool = MemorySearchTool(memory)
    del_tool = MemoryDeleteTool(memory)
    
    res_store = store_tool.execute({"text": "The sky is blue."})
    assert "Stored memory successfully with id:" in res_store
    mem_id = res_store.split("id: ")[1].strip()
    
    res_search = search_tool.execute({"query": "sky", "top_k": 2})
    assert "The sky is blue" in res_search
    
    del_tool.execute({"memory_id": mem_id})
    
    res_search_after = search_tool.execute({"query": "sky", "top_k": 2})
    assert "No relevant memories found" in res_search_after

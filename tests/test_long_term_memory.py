import tempfile
import pytest
from src.memory.long_term import LongTermMemory, ChromaVectorStore

@pytest.fixture
def ltm():
    tmpdir = tempfile.mkdtemp()
    store = ChromaVectorStore(tmpdir, "test_col")
    yield LongTermMemory(store)

def test_long_term_memory(ltm):
    record = ltm.store_memory("AgentOS is great", {"key": "value"})
    assert record.memory_id is not None
    assert ltm.count_memories() == 1
    
    results = ltm.retrieve_memories("AgentOS", 1)
    assert len(results) == 1
    assert results[0]["text"] == "AgentOS is great"
    assert results[0]["metadata"]["key"] == "value"
    
    ltm.delete_memory(record.memory_id)
    assert ltm.count_memories() == 0

import tempfile
import pytest
from src.memory.long_term import ChromaVectorStore

@pytest.fixture
def vector_store():
    tmpdir = tempfile.mkdtemp()
    store = ChromaVectorStore(tmpdir, "test_col")
    yield store
        
def test_vector_store_operations(vector_store):
    vector_store.add_documents(["id1", "id2"], ["hello world", "foo bar"], [{"meta": "1"}, {"meta": "2"}])
    assert vector_store.count_documents() == 2
    
    res = vector_store.search_documents("hello", 1)
    assert len(res) == 1
    assert res[0]["id"] == "id1"
    
    vector_store.delete_documents(["id1"])
    assert vector_store.count_documents() == 1
    
    vector_store.clear_collection()
    assert vector_store.count_documents() == 0

import tempfile
import pytest
from src.memory.long_term import ChromaVectorStore
from src.rag.retriever import Retriever

def test_retriever():
    tmpdir = tempfile.mkdtemp()
    store = ChromaVectorStore(tmpdir, "test_col")
    store.add_documents(["1", "2"], ["apple pie", "banana split"], [{"type": "food"}, {"type": "food"}])
    
    retriever = Retriever(store)
    res = retriever.retrieve("apple", top_k=1)
    assert len(res) == 1
    assert res[0]["text"] == "apple pie"
    
    store.clear_collection()
    empty_res = retriever.retrieve("apple")
    assert len(empty_res) == 0

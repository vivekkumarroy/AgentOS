import os
import tempfile
import pytest
from src.memory.long_term import ChromaVectorStore
from src.rag.pipeline import RAGPipeline

def test_rag_pipeline_ingest_and_retrieve():
    tmpdir = tempfile.mkdtemp()
    store = ChromaVectorStore(os.path.join(tmpdir, "db"), "test_col")
    workspace = os.path.join(tmpdir, "workspace")
    os.makedirs(workspace)
    
    pipeline = RAGPipeline(store, workspace, chunk_size=50, chunk_overlap=0)
    
    file_path = os.path.join(workspace, "doc.txt")
    with open(file_path, "w") as f:
        f.write("this is a test document with some content.")
        
    chunks = pipeline.ingest_document(file_path)
    assert chunks > 0
    
    results = pipeline.retrieve("test document", top_k=1)
    assert len(results) == 1
    assert "test document" in results[0]["text"]

import os
import tempfile
import pytest
from src.rag.document_loader import DocumentLoader

@pytest.fixture
def workspace_and_loader():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir, DocumentLoader(tmpdir)

def test_load_text_document(workspace_and_loader):
    tmpdir, loader = workspace_and_loader
    file_path = os.path.join(tmpdir, "test.txt")
    with open(file_path, "w") as f:
        f.write("text content")
        
    doc = loader.load_document(file_path)
    assert doc["text"] == "text content"
    assert doc["metadata"]["document_type"] == ".txt"

def test_load_document_outside_workspace(workspace_and_loader):
    tmpdir, loader = workspace_and_loader
    # creating a file outside
    with tempfile.TemporaryDirectory() as out_dir:
        file_path = os.path.join(out_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("text content")
            
        with pytest.raises(PermissionError):
            loader.load_document(file_path)

import pytest
import os
from pathlib import Path
from src.tools.filesystem import ReadFileTool, WriteFileTool, ListDirectoryTool, SearchFilesTool
from src.config import settings

@pytest.fixture
def workspace(tmp_path):
    settings.agent_workspace = str(tmp_path)
    return tmp_path

def test_write_and_read_file(workspace):
    writer = WriteFileTool()
    reader = ReadFileTool()
    
    res = writer.execute("test.txt", "hello world")
    assert res["success"] is True
    
    res2 = reader.execute("test.txt")
    assert res2["success"] is True
    assert res2["content"] == "hello world"

def test_path_traversal_blocked(workspace):
    writer = WriteFileTool()
    # Unix traversal
    res = writer.execute("../outside.txt", "hacked")
    assert res["success"] is False
    assert "outside the workspace" in res["error"]
    
    # Windows traversal
    res = writer.execute("..\\..\\windows_outside.txt", "hacked")
    assert res["success"] is False
    assert "outside the workspace" in res["error"]
    
    # Absolute path Windows
    res = writer.execute("C:\\Windows\\System32\\config.txt", "hacked")
    assert res["success"] is False
    assert "outside the workspace" in res["error"]
    
    # Absolute path Unix style
    res = writer.execute("/etc/passwd", "hacked")
    assert res["success"] is False
    assert "outside the workspace" in res["error"]

def test_list_and_search(workspace):
    writer = WriteFileTool()
    writer.execute("dir/file1.txt", "apple")
    writer.execute("dir/file2.txt", "banana")
    
    lister = ListDirectoryTool()
    res = lister.execute("dir")
    assert res["success"] is True
    assert set(res["items"]) == {"file1.txt", "file2.txt"}
    
    searcher = SearchFilesTool()
    res = searcher.execute("dir", "apple")
    assert res["success"] is True
    assert len(res["matches"]) == 1
    assert "file1.txt" in res["matches"][0]

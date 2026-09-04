import pytest
import httpx
from src.tools.web import WebSearchTool, WebExtractTool
from src.config import settings

def test_web_search_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "search_api_key", "")
    tool = WebSearchTool()
    res = tool.execute("test")
    assert res["success"] is False
    assert "Missing SEARCH_API_KEY" in res["error"]

def test_web_extract_mocked(monkeypatch):
    class MockResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse("<html><head><title>Test Title</title></head><body><p>Hello world</p></body></html>")
        
    monkeypatch.setattr(httpx, "get", mock_get)
    tool = WebExtractTool()
    res = tool.execute("http://example.com")
    
    assert res["success"] is True
    assert res["title"] == "Test Title"
    assert "Hello world" in res["text"]

def test_web_extract_timeout(monkeypatch):
    def mock_get_timeout(*args, **kwargs):
        raise httpx.TimeoutException("Timeout")
        
    monkeypatch.setattr(httpx, "get", mock_get_timeout)
    tool = WebExtractTool()
    res = tool.execute("http://example.com")
    
    assert res["success"] is False
    assert "timed out" in res["error"]

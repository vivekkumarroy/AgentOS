import pytest
from pydantic import BaseModel
from src.tools.base import BaseTool
from src.tools.registry import ToolRegistry

class DummyInput(BaseModel):
    pass

class DummyTool(BaseTool):
    name = "dummy"
    description = "desc"
    input_schema = DummyInput
    
    def execute(self, **kwargs):
        return {"success": True}

def test_tool_registry():
    registry = ToolRegistry()
    tool = DummyTool()
    
    registry.register(tool)
    assert registry.has("dummy")
    assert registry.get("dummy") == tool
    assert "dummy" in registry.list_tools()
    
    with pytest.raises(ValueError):
        registry.register(tool)
        
    with pytest.raises(KeyError):
        registry.get("unknown")
        
    schemas = registry.get_all_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "dummy"

import json
from src.tools.registry import ToolRegistry
from src.execution.executor import Executor
from src.models.state import ToolCall
from src.tools.filesystem import WriteFileTool
from src.config import settings

def test_executor(tmp_path):
    settings.agent_workspace = str(tmp_path)
    
    registry = ToolRegistry()
    registry.register(WriteFileTool())
    
    executor = Executor(registry)
    
    call = ToolCall(tool_name="write_file", arguments={"path": "test.txt", "content": "exec test"})
    obs = executor.execute_tool(call)
    
    assert obs.status == "SUCCESS"
    res_dict = json.loads(obs.result)
    assert res_dict["success"] is True
    
    # Invalid arguments
    bad_call = ToolCall(tool_name="write_file", arguments={"wrong": "arg"})
    obs = executor.execute_tool(bad_call)
    assert obs.status == "FAILED"
    assert "Invalid arguments" in obs.error
    
    # Unknown tool
    unknown_call = ToolCall(tool_name="unknown", arguments={})
    obs = executor.execute_tool(unknown_call)
    assert obs.status == "FAILED"
    assert "Unknown tool" in obs.error

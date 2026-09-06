import pytest
from pydantic import ValidationError
from src.models.agent import AgentProfile
from src.orchestration.registry import AgentRegistry
from src.orchestration.factory import SubAgentFactory
from src.tools.delegation import DelegateTaskTool
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool
from src.llm.client import LLMClient
from src.tracing.tracer import NoOpTracer
from typing import Any
from pydantic import BaseModel

class DummyToolArgs(BaseModel):
    pass

class DummyTool(BaseTool):
    name = "dummy"
    description = "Dummy tool"
    input_schema = DummyToolArgs

    def execute(self, **kwargs: Any) -> Any:
        return {"success": True, "result": "dummy"}

class FailingTool(BaseTool):
    name = "failing"
    description = "Always fails"
    input_schema = DummyToolArgs

    def execute(self, **kwargs: Any) -> Any:
        return {"success": False, "error": "simulated failure"}

def test_agent_profile_validation():
    # Valid
    p = AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=["t1"])
    assert p.name == "test"
    
    # Empty name
    with pytest.raises(ValidationError):
        AgentProfile(name="", description="desc", system_prompt="sys", allowed_tools=["t1"])
        
    # Empty tools
    with pytest.raises(ValidationError):
        AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=[])

def test_agent_registry():
    r = AgentRegistry()
    p = AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=["t1"])
    
    # Registration & Lookup
    r.register(p)
    assert r.exists("test")
    assert r.get("test") == p
    
    # Duplicate handling
    with pytest.raises(ValueError):
        r.register(p)
        
    # Listing
    assert len(r.list()) == 1
    assert r.list()[0].name == "test"

def test_delegate_task_tool_unknown_agent():
    r = AgentRegistry()
    f = SubAgentFactory(ToolRegistry(), LLMClient())
    t = DelegateTaskTool(r, f)
    
    res = t.execute(agent_name="unknown", task_description="do something")
    assert res["success"] is False
    assert "not registered" in res["error"]

def test_delegation_depth_protection():
    r = AgentRegistry()
    p = AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=["dummy"])
    r.register(p)
    
    # Setup global registry with dummy tool
    tr = ToolRegistry()
    tr.register(DummyTool())
    
    f = SubAgentFactory(tr, LLMClient())
    t = DelegateTaskTool(r, f)
    
    from src.tracing.context import current_delegation_depth
    token = current_delegation_depth.set(2)  # Assuming max is 2
    
    try:
        res = t.execute(agent_name="test", task_description="do something")
        assert res["success"] is False
        assert "Max delegation depth" in res["error"]
    finally:
        current_delegation_depth.reset(token)

def test_worker_allowed_tools_restriction():
    tr = ToolRegistry()
    tr.register(DummyTool())
    tr.register(FailingTool())
    
    p = AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=["dummy"])
    f = SubAgentFactory(tr, LLMClient())
    
    worker = f.create_worker(p, parent_run_id="r1", delegation_depth=1)
    
    # The worker's executor should only have 'dummy', not 'failing'
    assert worker.executor.registry.has("dummy")
    assert not worker.executor.registry.has("failing")

def test_worker_cannot_use_disallowed_tools():
    tr = ToolRegistry()
    tr.register(DummyTool())
    tr.register(FailingTool())
    
    p = AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=["dummy"])
    f = SubAgentFactory(tr, LLMClient())
    worker = f.create_worker(p, parent_run_id="r1", delegation_depth=1)
    
    # Create an observation for an unknown tool call
    from src.models.state import ToolCall
    tc = ToolCall(tool_name="failing")
    
    obs = worker.executor.execute_tool(tc)
    assert obs.status == "FAILED"
    assert "Unknown tool" in obs.error

def test_parent_child_trace_correlation():
    tr = ToolRegistry()
    tr.register(DummyTool())
    p = AgentProfile(name="test", description="desc", system_prompt="sys", allowed_tools=["dummy"])
    
    class MockTracer(NoOpTracer):
        def __init__(self):
            self.emitted = []
        def emit(self, event):
            self.emitted.append(event)
            
    mt = MockTracer()
    f = SubAgentFactory(tr, LLMClient(), tracer=mt)
    worker = f.create_worker(p, parent_run_id="parent123", delegation_depth=1)
    
    from src.models.state import Task, TaskStatus
    task = Task(task_id="t1", description="desc", expected_output="out")
    worker.memory.get_state().tasks_state["t1"] = task
    worker.run_task_with_recovery("t1")
    
    # Verify trace events from worker got parent_run_id injected
    assert len(mt.emitted) > 0
    for e in mt.emitted:
        assert e.parent_run_id == "parent123"
        assert e.subagent_name == "test"
        assert e.delegation_depth == 1

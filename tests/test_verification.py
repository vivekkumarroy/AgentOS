from src.verification.verifier import VerificationEngine
from src.models.state import Task, ToolCall, Observation, VerificationResult

class MockLLMClient:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    def generate_structured_output(self, prompt, schema_cls):
        resp = self.responses[self.call_count]
        self.call_count += 1
        return schema_cls(**resp)

def test_verification_success():
    llm = MockLLMClient([{"success": True, "reason": "Looks good"}])
    verifier = VerificationEngine(llm)
    task = Task(task_id="t1", description="desc", expected_output="out")
    tool = ToolCall(tool_name="tool")
    obs = Observation(status="SUCCESS", result="data")
    
    res = verifier.verify(task, tool, obs)
    assert res.success is True

def test_verification_tool_failure_fast_path():
    llm = MockLLMClient([])
    verifier = VerificationEngine(llm)
    task = Task(task_id="t1", description="desc", expected_output="out")
    tool = ToolCall(tool_name="tool")
    obs = Observation(status="FAILED", result="", error="broke")
    
    res = verifier.verify(task, tool, obs)
    assert res.success is False
    assert "Tool execution failed" in res.reason
    assert llm.call_count == 0

from src.recovery.replanner import RecoveryPlanner
from src.models.state import Task, FailureDiagnosis, FailureCategory

class MockLLMClient:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    def generate_structured_output(self, prompt, schema_cls):
        resp = self.responses[self.call_count]
        self.call_count += 1
        return schema_cls(**resp)

def test_recovery_plan_creation():
    llm = MockLLMClient([{
        "original_task_id": "t1",
        "strategy": "try again",
        "revised_task_description": "new desc",
        "retry_allowed": True
    }])
    replanner = RecoveryPlanner(llm)
    task = Task(task_id="t1", description="desc", expected_output="out")
    diag = FailureDiagnosis(
        failure_type=FailureCategory.TIMEOUT,
        reason="too slow",
        affected_task_id="t1",
        recoverable=True,
        suggested_recovery="increase timeout"
    )
    
    plan = replanner.create_recovery_plan(task, diag)
    assert plan.retry_allowed is True
    assert plan.revised_task_description == "new desc"

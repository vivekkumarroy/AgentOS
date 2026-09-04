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

def test_retry_budget_exhausted():
    llm = MockLLMClient([])
    replanner = RecoveryPlanner(llm)
    task = Task(task_id="t1", description="desc", expected_output="out", retry_count=3, max_retries=3)
    diag = FailureDiagnosis(
        failure_type=FailureCategory.TIMEOUT,
        reason="too slow",
        affected_task_id="t1",
        recoverable=True,
        suggested_recovery="retry"
    )
    
    plan = replanner.create_recovery_plan(task, diag)
    assert plan.retry_allowed is False
    assert "budget exhausted" in plan.strategy.lower()
    assert llm.call_count == 0

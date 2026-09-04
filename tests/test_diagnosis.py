from src.recovery.diagnosis import FailureDiagnosisEngine
from src.models.state import Task, Observation, VerificationResult, FailureCategory

class MockLLMClient:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    def generate_structured_output(self, prompt, schema_cls):
        resp = self.responses[self.call_count]
        self.call_count += 1
        return schema_cls(**resp)

def test_diagnosis_file_not_found():
    llm = MockLLMClient([{
        "failure_type": FailureCategory.FILE_NOT_FOUND,
        "reason": "missing",
        "affected_task_id": "t1",
        "recoverable": True,
        "suggested_recovery": "search"
    }])
    diagnoser = FailureDiagnosisEngine(llm)
    task = Task(task_id="t1", description="desc", expected_output="out")
    obs = Observation(status="SUCCESS", result="no file")
    ver = VerificationResult(success=False, reason="missing file")
    
    diag = diagnoser.diagnose(task, obs, ver)
    assert diag.failure_type == FailureCategory.FILE_NOT_FOUND
    assert diag.recoverable is True

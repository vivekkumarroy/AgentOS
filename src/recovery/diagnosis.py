import logging
from ..models.state import Task, Observation, VerificationResult, FailureDiagnosis
from ..llm.client import LLMClient

logger = logging.getLogger(__name__)

DIAGNOSIS_PROMPT = """You are a failure diagnosis engine.
The following task failed to verify successfully. 

Task description: {task_description}
Observation: {observation}
Verification Reason: {verification_reason}

Analyze the failure and categorize it into a FailureDiagnosis structure.
Identify if it is recoverable, and suggest a recovery strategy.
"""

class FailureDiagnosisEngine:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def diagnose(self, task: Task, observation: Observation, verification: VerificationResult) -> FailureDiagnosis:
        logger.info(f"Diagnosing failure for task: {task.task_id}")
        
        prompt = DIAGNOSIS_PROMPT.format(
            task_description=task.description,
            observation=observation.result if observation.status == "SUCCESS" else (observation.error or observation.result),
            verification_reason=verification.reason
        )
        
        try:
            diagnosis = self.llm.generate_structured_output(prompt, FailureDiagnosis)
            diagnosis.affected_task_id = task.task_id
            logger.info(f"Diagnosis completed. Category: {diagnosis.failure_type.value}, Recoverable: {diagnosis.recoverable}")
            return diagnosis
        except Exception as e:
            logger.error(f"Diagnosis failed: {e}")
            from ..models.state import FailureCategory
            return FailureDiagnosis(
                failure_type=FailureCategory.UNKNOWN_ERROR,
                reason=f"Diagnosis engine failed: {e}",
                affected_task_id=task.task_id,
                recoverable=False,
                suggested_recovery="Manual intervention required."
            )

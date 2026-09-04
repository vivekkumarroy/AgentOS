import logging
from ..models.state import Task, FailureDiagnosis, RecoveryPlan
from ..llm.client import LLMClient

logger = logging.getLogger(__name__)

REPLAN_PROMPT = """You are a recovery replanner.
A task failed and was diagnosed. 

Original Task: {task_description}
Diagnosis Reason: {diagnosis_reason}
Suggested Recovery: {suggested_recovery}
Current Retry Count: {retry_count} / {max_retries}

Create a RecoveryPlan. Revise the task description to incorporate the recovery strategy so the agent knows what to do differently.
If we are out of retries (retry_count >= max_retries), set retry_allowed to false.
"""

class RecoveryPlanner:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def create_recovery_plan(self, task: Task, diagnosis: FailureDiagnosis) -> RecoveryPlan:
        logger.info(f"Creating recovery plan for task: {task.task_id}")
        
        if task.retry_count >= task.max_retries:
            logger.info("Retry budget exhausted.")
            return RecoveryPlan(
                original_task_id=task.task_id,
                strategy="Retry budget exhausted.",
                revised_task_description=task.description,
                retry_allowed=False
            )
            
        prompt = REPLAN_PROMPT.format(
            task_description=task.description,
            diagnosis_reason=diagnosis.reason,
            suggested_recovery=diagnosis.suggested_recovery,
            retry_count=task.retry_count,
            max_retries=task.max_retries
        )
        
        try:
            plan = self.llm.generate_structured_output(prompt, RecoveryPlan)
            plan.original_task_id = task.task_id
            logger.info(f"Recovery plan created. Retry allowed: {plan.retry_allowed}")
            return plan
        except Exception as e:
            logger.error(f"Replanner failed: {e}")
            return RecoveryPlan(
                original_task_id=task.task_id,
                strategy=f"Fallback recovery due to replanner error: {e}",
                revised_task_description=task.description,
                retry_allowed=False
            )

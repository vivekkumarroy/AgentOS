import logging
from pydantic import ValidationError
from ..models.state import Task, ToolCall, Observation, VerificationResult
from ..llm.client import LLMClient
import json

logger = logging.getLogger(__name__)

VERIFIER_PROMPT = """You are a verification engine for an autonomous agent.
Your objective is to determine whether the task succeeded based on the observation.

Task description: {task_description}
Expected output: {expected_output}
Tool called: {tool_name}
Tool arguments: {tool_arguments}
Observation status: {observation_status}
Observation result: {observation_result}
Observation error: {observation_error}

Analyze the information. 
Did the tool execution actually fulfill the task's expected output?
(Note: A tool might successfully execute but not fulfill the task, e.g. finding 0 results when results were expected).
Return a VerificationResult structure.
"""

class VerificationEngine:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def verify(self, task: Task, tool_call: ToolCall, observation: Observation) -> VerificationResult:
        logger.info(f"Verifying task: {task.task_id}")
        
        # Fast path: If the tool itself errored out completely, it's a failure.
        if observation.status == "FAILED" or observation.error:
            return VerificationResult(
                success=False,
                reason=f"Tool execution failed: {observation.error or observation.result}"
            )
            
        prompt = VERIFIER_PROMPT.format(
            task_description=task.description,
            expected_output=task.expected_output,
            tool_name=tool_call.tool_name,
            tool_arguments=json.dumps(tool_call.arguments),
            observation_status=observation.status,
            observation_result=observation.result,
            observation_error=observation.error or "None"
        )
        
        try:
            result = self.llm.generate_structured_output(prompt, VerificationResult)
            logger.info(f"Verification completed. Success: {result.success}")
            return result
        except ValidationError as e:
            logger.error(f"Verification output validation failed: {e}")
            return VerificationResult(success=False, reason="Failed to validate verification output.")
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return VerificationResult(success=False, reason=f"Verification engine error: {e}")

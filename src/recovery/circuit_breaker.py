import logging
from typing import List
from ..models.state import ToolCall, Task

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, max_identical_actions: int = 3):
        self.max_identical_actions = max_identical_actions

    def check_loop(self, current_tool_call: ToolCall, action_history: List[ToolCall]) -> bool:
        """
        Returns True if the system is stuck in a loop (repeating the exact same action),
        False otherwise.
        """
        if not action_history:
            return False
            
        consecutive_matches = 0
        for past_action in reversed(action_history):
            if (past_action.tool_name == current_tool_call.tool_name and 
                past_action.arguments == current_tool_call.arguments):
                consecutive_matches += 1
            else:
                break
                
        is_loop = consecutive_matches >= self.max_identical_actions - 1
        if is_loop:
            logger.warning(f"CIRCUIT_BREAKER_TRIGGERED: Tool {current_tool_call.tool_name} with arguments {current_tool_call.arguments} repeated {consecutive_matches + 1} times.")
        return is_loop

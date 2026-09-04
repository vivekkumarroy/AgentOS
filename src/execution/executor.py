import logging
import json
from ..tools.registry import ToolRegistry
from ..models.state import ToolCall, Observation
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_tool(self, tool_call: ToolCall) -> Observation:
        logger.info(f"Executing tool: {tool_call.tool_name}")
        
        if not self.registry.has(tool_call.tool_name):
            error_msg = f"Unknown tool: '{tool_call.tool_name}'"
            logger.error(error_msg)
            return Observation(result="", status="FAILED", error=error_msg)
            
        tool = self.registry.get(tool_call.tool_name)
        
        try:
            validated_args = tool.input_schema(**tool_call.arguments)
        except ValidationError as e:
            error_msg = f"Invalid arguments for tool '{tool.name}': {e}"
            logger.error(error_msg)
            return Observation(result="", status="FAILED", error=error_msg)
            
        try:
            result_dict = tool.execute(**validated_args.model_dump())
            
            success = result_dict.get("success", False)
            status = "SUCCESS" if success else "FAILED"
            error = result_dict.get("error", None)
            
            result_str = json.dumps(result_dict)
            return Observation(result=result_str, status=status, error=error)
        except Exception as e:
            error_msg = f"Execution error in tool '{tool.name}': {e}"
            logger.error(error_msg)
            return Observation(result="", status="FAILED", error=error_msg)

from typing import Dict, List, Any
from .base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str):
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> BaseTool:
        if tool_name not in self._tools:
            raise KeyError(f"Unknown tool: '{tool_name}'")
        return self._tools[tool_name]

    def has(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema_dict() for tool in self._tools.values()]

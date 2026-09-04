import abc
from typing import Any, Type, Dict
from pydantic import BaseModel

class BaseTool(abc.ABC):
    name: str
    description: str
    input_schema: Type[BaseModel]

    @abc.abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Executes the tool with the validated arguments."""
        pass
        
    def to_schema_dict(self) -> Dict[str, Any]:
        """Returns the schema representation for LLM ingestion."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema()
        }

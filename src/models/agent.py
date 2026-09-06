from pydantic import BaseModel, Field, field_validator
from typing import List

class AgentProfile(BaseModel):
    name: str = Field(..., description="Unique name of the agent profile.")
    description: str = Field(..., description="Description of the agent's capabilities.")
    system_prompt: str = Field(..., description="System instructions for the agent.")
    allowed_tools: List[str] = Field(..., description="List of tool names this agent is allowed to execute.")
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v

    @field_validator('allowed_tools')
    @classmethod
    def allowed_tools_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Agent must have at least one allowed tool (e.g. ['python'] or ['calculator'])")
        return v

from typing import Dict, List, Optional
from ..models.agent import AgentProfile

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentProfile] = {}

    def register(self, profile: AgentProfile) -> None:
        """Register a new agent profile. Rejects duplicates."""
        if profile.name in self._agents:
            raise ValueError(f"Agent profile with name '{profile.name}' is already registered.")
        self._agents[profile.name] = profile

    def get(self, agent_name: str) -> Optional[AgentProfile]:
        """Retrieve an agent profile by name."""
        return self._agents.get(agent_name)

    def list(self) -> List[AgentProfile]:
        """List all registered agent profiles."""
        return list(self._agents.values())

    def exists(self, agent_name: str) -> bool:
        """Check if an agent profile exists."""
        return agent_name in self._agents

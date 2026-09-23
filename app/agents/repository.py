from typing import Protocol

from app.agents.model import Agent


class AgentRepository(Protocol):
    def validate_schema(self) -> None:
        ...

    def create(self, agent: Agent) -> None:
        ...

    def save(self, agent: Agent) -> None:
        ...

    def get(self, agent_id: str, owner_id: str | None = None) -> Agent | None:
        ...

    def list_agents(self, owner_id: str | None = None) -> list[Agent]:
        ...

    def delete(self, agent_id: str, owner_id: str | None = None) -> bool:
        ...
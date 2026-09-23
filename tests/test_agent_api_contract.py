import asyncio

from app import main
from app.agents.model import Agent


class FakeRegistry:
    def __init__(self):
        self.saved = []

    def save(self, agent):
        self.saved.append(agent)

    def list_agents(self, owner_id=None):
        return [agent for agent in self.saved if agent.owner_id == owner_id]


def test_create_agent_maps_public_user_id_to_owner_id(monkeypatch):
    registry = FakeRegistry()
    monkeypatch.setattr(main, "agent_registry", registry)
    monkeypatch.setattr(main.knowledge_service, "reindex_agent", lambda *args: None)

    response = asyncio.run(
        main.create_agent(
            main.AgentCreateRequest(
                name="Support",
                goal="Resolve requests",
                description="Customer support",
                enabledTools=["search"],
                knowledgeSources=[{"id": "faq-1"}],
                channels=["voice"],
                configurationFlag={"enabled": True},
            ),
            user_id="owner-a",
        )
    )

    saved = registry.saved[0]
    assert saved.owner_id == "owner-a"
    assert saved.capabilities == ["search"]
    assert saved.knowledge_sources == [{"id": "faq-1"}]
    assert saved.channels == ["voice"]
    assert saved.configuration["configurationFlag"] == {"enabled": True}
    assert response["owner_id"] == "owner-a"
    assert response["name"] == "Support"


def test_list_agents_returns_only_requested_owner_and_flattened_fields(monkeypatch):
    registry = FakeRegistry()
    owner_agent = Agent(
        name="Owner agent",
        goal="Help",
        owner_id="owner-a",
        configuration={"agentType": "support"},
    )
    other_agent = Agent(name="Other agent", goal="Help", owner_id="owner-b")
    registry.saved = [owner_agent, other_agent]
    monkeypatch.setattr(main, "agent_registry", registry)

    response = asyncio.run(main.list_agents(user_id="owner-a"))

    assert response["total"] == 1
    assert response["items"] == [
        {
            "agentType": "support",
            "id": owner_agent.id,
            "name": "Owner agent",
            "goal": "Help",
            "description": "",
            "capabilities": [],
            "knowledge_sources": [],
            "channels": [],
            "status": "DRAFT",
            "version": "1.0",
            "owner_id": "owner-a",
            "created_at": owner_agent.created_at,
            "updated_at": owner_agent.updated_at,
        }
    ]
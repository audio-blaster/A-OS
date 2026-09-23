from dataclasses import asdict

from app.agents.model import Agent
from app.agents.registry import AgentRegistry
from app.agents.supabase_repository import (
    SupabaseAgentRepository,
    agent_to_row,
    row_to_agent,
)


class FakeResponse:
    def __init__(self, data, error=None):
        self.data = data
        self.error = error


class FakeQuery:
    def __init__(self, table, operation, payload=None):
        self.table = table
        self.operation = operation
        self.payload = payload
        self.filters = []

    def select(self, _columns):
        return self

    def upsert(self, row):
        self.operation = "upsert"
        self.payload = row
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, _count):
        return self

    def execute(self):
        if self.operation == "upsert":
            self.table.rows[self.payload["id"]] = self.payload
            return FakeResponse([self.payload])

        matching = [
            row for row in self.table.rows.values()
            if all(row[field] == value for field, value in self.filters)
        ]
        if self.operation == "delete":
            for row in matching:
                del self.table.rows[row["id"]]
        return FakeResponse(matching)


class FakeTable:
    def __init__(self):
        self.rows = {}

    def table(self, _name):
        return self

    def select(self, _columns):
        return FakeQuery(self, "select")

    def upsert(self, row):
        return FakeQuery(self, "upsert", row)

    def delete(self):
        return FakeQuery(self, "delete")


def make_agent(owner_id=None):
    return Agent(
        id="legacy-agent-id",
        owner_id=owner_id,
        name="Agent",
        goal="Resolve requests",
        description="Support",
        capabilities=["search"],
        knowledge_sources=[{"id": "source-1", "type": "faq"}],
        channels=["voice"],
        configuration={
            "name": "nested name",
            "knowledgeSources": [{"id": "nested-source"}],
            "futureSetting": {"enabled": True},
        },
        status="PUBLISHED",
        version="1.0",
        created_at="2026-09-21T00:00:00",
        updated_at="2026-09-21T01:00:00",
    )


def test_agent_to_row_preserves_all_fields_and_json_values():
    agent = make_agent(owner_id="user-1")

    assert agent_to_row(agent) == asdict(agent)
    assert agent_to_row(agent)["configuration"]["futureSetting"] == {"enabled": True}


def test_row_to_agent_preserves_all_fields_and_configuration():
    agent = make_agent(owner_id="user-1")

    assert row_to_agent(agent_to_row(agent)) == agent


def test_agent_to_row_rejects_ownerless_persistent_agents():
    try:
        agent_to_row(make_agent())
    except ValueError as error:
        assert str(error) == "Persisted agents require owner_id"
    else:
        raise AssertionError("ownerless agents must not be serialized for Supabase")


def test_repository_crud_and_owner_filtering():
    client = FakeTable()
    repository = SupabaseAgentRepository(client)
    owned = make_agent(owner_id="user-1")
    legacy = make_agent(owner_id="user-2")
    legacy.id = "legacy-agent"

    repository.create(owned)
    repository.save(legacy)

    assert repository.get(owned.id, owner_id="user-1") == owned
    assert repository.get(owned.id, owner_id="other-user") is None
    assert repository.list_agents(owner_id="user-1") == [owned]
    assert repository.list_agents(owner_id="other-user") == []
    assert repository.delete(owned.id, owner_id="other-user") is False
    assert repository.delete(owned.id, owner_id="user-1") is True
    assert repository.get(owned.id) is None
    assert repository.get(legacy.id) == legacy


def test_repository_schema_validation_uses_the_canonical_columns():
    repository = SupabaseAgentRepository(FakeTable())

    repository.validate_schema()


class PermissionErrorResponse:
    code = "42501"

    def __str__(self):
        return "permission denied for table agents"


class PermissionErrorQuery:
    def select(self, _columns):
        return self

    def limit(self, _count):
        return self

    def execute(self):
        return FakeResponse([], error=PermissionErrorResponse())


class PermissionErrorClient:
    def table(self, _name):
        return PermissionErrorQuery()


def test_repository_schema_validation_distinguishes_permission_errors():
    repository = SupabaseAgentRepository(PermissionErrorClient())

    try:
        repository.validate_schema()
    except RuntimeError as error:
        message = str(error)
        assert "does not have permission" in message
        assert "public.agents" in message
        assert "missing" not in message.lower()
    else:
        raise AssertionError("permission errors must fail startup validation")


def test_registry_can_use_repository_and_still_write_definition(tmp_path):
    client = FakeTable()
    repository = SupabaseAgentRepository(client)
    registry = AgentRegistry(repository=repository)
    registry.storage_path = tmp_path
    agent = make_agent(owner_id="user-1")

    registry.save(agent)

    assert repository.get(agent.id) == agent
    assert (tmp_path / f"{agent.id}.AGENT.md").exists()
    assert not (tmp_path / f"{agent.id}.json").exists()


def test_default_registry_keeps_json_persistence_compatible(tmp_path):
    registry = AgentRegistry()
    registry.storage_path = tmp_path
    agent = make_agent()

    registry.save(agent)

    assert registry.get(agent.id) == agent
    assert registry.list_agents() == [agent]
    assert registry.delete(agent.id) is True
    assert registry.get(agent.id) is None
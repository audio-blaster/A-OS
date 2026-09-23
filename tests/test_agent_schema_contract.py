from pathlib import Path

from app.agents.model import Agent
from app.agents.supabase_repository import AGENT_COLUMNS, agent_to_row


def make_agent():
    return Agent(
        name="Contract agent",
        goal="Preserve the persistence contract",
        owner_id="11111111-1111-1111-1111-111111111111",
        capabilities=["search"],
        knowledge_sources=[{"id": "source-1", "type": "faq"}],
        channels=["voice"],
        configuration={"nested": {"enabled": True}},
        status="PUBLISHED",
    )


def test_agent_row_keys_match_canonical_columns():
    assert set(agent_to_row(make_agent())) == set(AGENT_COLUMNS)


def test_agent_row_round_trip_values_cover_every_canonical_field():
    agent = make_agent()
    row = agent_to_row(agent)

    assert row["id"] == agent.id
    assert row["owner_id"] == agent.owner_id
    assert row["name"] == agent.name
    assert row["goal"] == agent.goal
    assert row["description"] == agent.description
    assert row["capabilities"] == agent.capabilities
    assert row["knowledge_sources"] == agent.knowledge_sources
    assert row["channels"] == agent.channels
    assert row["configuration"] == agent.configuration
    assert row["status"] == agent.status
    assert row["version"] == agent.version
    assert row["created_at"] == agent.created_at
    assert row["updated_at"] == agent.updated_at


def test_corrective_migration_mentions_every_canonical_column():
    migration = Path(__file__).parents[1] / "supabase" / "migrations" / "20260922000000_reconcile_agents_schema.sql"
    sql = migration.read_text(encoding="utf-8")

    for column in AGENT_COLUMNS:
        assert column in sql
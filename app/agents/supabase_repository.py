import os
import re

from app.agents.model import Agent


AGENT_COLUMNS = (
    "id",
    "owner_id",
    "name",
    "goal",
    "description",
    "capabilities",
    "knowledge_sources",
    "channels",
    "configuration",
    "status",
    "version",
    "created_at",
    "updated_at",
)


def agent_to_row(agent: Agent) -> dict:
    if not agent.owner_id:
        raise ValueError("Persisted agents require owner_id")

    return {
        "id": agent.id,
        "owner_id": agent.owner_id,
        "name": agent.name,
        "goal": agent.goal,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "knowledge_sources": agent.knowledge_sources,
        "channels": agent.channels,
        "configuration": agent.configuration,
        "status": agent.status,
        "version": agent.version,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
    }


def row_to_agent(row: dict) -> Agent:
    return Agent(
        id=row["id"],
        owner_id=row["owner_id"],
        name=row["name"],
        goal=row["goal"],
        description=row["description"],
        capabilities=row["capabilities"],
        knowledge_sources=row["knowledge_sources"],
        channels=row["channels"],
        configuration=row["configuration"],
        status=row["status"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SupabaseAgentRepository:
    """Persistence adapter for Agent rows in Supabase."""

    def __init__(self, client, table_name: str = "agents"):
        self.client = client
        self.table_name = table_name

    def _table(self):
        return self.client.table(self.table_name)

    @staticmethod
    def _rows(response) -> list[dict]:
        return list(getattr(response, "data", None) or [])

    @staticmethod
    def _error_code(error) -> str | None:
        if isinstance(error, dict):
            code = error.get("code")
        else:
            code = getattr(error, "code", None)
        return str(code) if code else None

    @staticmethod
    def _missing_columns(error) -> list[str]:
        message = str(error)
        patterns = (
            r"column\s+(?:[\w.]+\.)?[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?\s+does not exist",
            r"Could not find the '([A-Za-z_][A-Za-z0-9_]*)' column",
        )
        for pattern in patterns:
            matches = re.findall(pattern, message, flags=re.IGNORECASE)
            if matches:
                return sorted(set(matches))
        return list(AGENT_COLUMNS)

    def _raise_schema_validation_error(self, error) -> None:
        def raise_runtime_error(message: str) -> None:
            if isinstance(error, BaseException):
                raise RuntimeError(message) from error
            raise RuntimeError(message)

        code = self._error_code(error)
        if code == "42501":
            raise_runtime_error(
                "Supabase backend client does not have permission to access "
                "public.agents; verify the configured Supabase key and database grants."
            )

        if code in {"42703", "42P01", "PGRST204", "PGRST205"}:
            missing = ", ".join(self._missing_columns(error))
            raise_runtime_error(
                "Supabase public.agents schema is missing required column(s): "
                + missing
            )

        raise_runtime_error(
            "Supabase Agent schema validation failed"
            + (f" (code {code})" if code else "")
            + f": {error}"
        )

    def validate_schema(self) -> None:
        """Fail during startup when the deployed table misses a contract column."""
        try:
            query = self._table().select(",".join(AGENT_COLUMNS))
            if hasattr(query, "limit"):
                query = query.limit(0)
            response = query.execute()
        except Exception as error:
            self._raise_schema_validation_error(error)

        response_error = getattr(response, "error", None)
        if response_error:
            self._raise_schema_validation_error(response_error)

    def save(self, agent: Agent) -> None:
        self._table().upsert(agent_to_row(agent)).execute()

    def create(self, agent: Agent) -> None:
        self.save(agent)

    def get(self, agent_id: str, owner_id: str | None = None) -> Agent | None:
        query = self._table().select(",".join(AGENT_COLUMNS)).eq("id", agent_id)
        if owner_id is not None:
            query = query.eq("owner_id", owner_id)

        rows = self._rows(query.execute())
        return row_to_agent(rows[0]) if rows else None

    def list_agents(self, owner_id: str | None = None) -> list[Agent]:
        query = self._table().select(",".join(AGENT_COLUMNS))
        if owner_id is not None:
            query = query.eq("owner_id", owner_id)

        return [row_to_agent(row) for row in self._rows(query.execute())]

    def delete(self, agent_id: str, owner_id: str | None = None) -> bool:
        if self.get(agent_id, owner_id=owner_id) is None:
            return False

        query = self._table().delete().eq("id", agent_id)
        if owner_id is not None:
            query = query.eq("owner_id", owner_id)

        query.execute()
        return True


def create_supabase_agent_repository(
    url: str | None = None,
    key: str | None = None,
) -> SupabaseAgentRepository:
    """Create an explicitly requested repository from environment settings."""
    from supabase import create_client

    resolved_url = url or os.environ.get("SUPABASE_URL")
    resolved_key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get(
        "SUPABASE_ANON_KEY"
    )
    if not resolved_url or not resolved_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY are required"
        )

    return SupabaseAgentRepository(create_client(resolved_url, resolved_key))
import json
from pathlib import Path
from dataclasses import asdict

from app.agents.model import Agent


class AgentRegistry:

    def __init__(self):

        self.storage_path = Path(
            "data/agents"
        )

        self.storage_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def save(self, agent: Agent):

        file_path = (
            self.storage_path /
            f"{agent.id}.json"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                asdict(agent),
                file,
                indent=4
            )

        configuration = agent.configuration
        definition = [
            f"# {agent.name}",
            "",
            f"## Role / Agent Type\n{configuration.get('agentType', '')}",
            f"## Description\n{agent.description}",
            f"## Purpose\n{configuration.get('purpose', '')}",
            f"## Goals / Responsibilities\n{configuration.get('goals') or agent.goal}",
            "## Interaction Principles",
            f"- Personality: {configuration.get('personality', '')}",
            f"- Tone: {configuration.get('tone', '')}",
            f"- Conversation style: {configuration.get('conversationStyle', '')}",
        ]

        allowed_topics = configuration.get("allowedTopics", [])
        restricted_topics = configuration.get("restrictedTopics", [])

        if allowed_topics:
            definition.extend([
                "",
                "## Allowed Topics",
                *[f"- {item}" for item in allowed_topics],
            ])

        if restricted_topics:
            definition.extend([
                "",
                "## Restricted Topics",
                *[f"- {item}" for item in restricted_topics],
            ])

        escalation_rules = configuration.get("escalationRules", "")
        handoff_conditions = configuration.get("humanHandoffConditions", "")

        if escalation_rules or handoff_conditions:
            definition.append("")
            definition.append("## Escalation / Handoff")
            if escalation_rules:
                definition.append(f"Escalation rules: {escalation_rules}")
            if handoff_conditions:
                definition.append(f"Human handoff conditions: {handoff_conditions}")

        definition_path = (
            self.storage_path /
            f"{agent.id}.AGENT.md"
        )

        definition_path.write_text(
            "\n".join(definition) + "\n",
            encoding="utf-8"
        )

    def get(self, agent_id: str, owner_id: str | None = None):

        file_path = (
            self.storage_path /
            f"{agent_id}.json"
        )

        if not file_path.exists():
            return None

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        agent = Agent(**data)

        if owner_id is not None:
            if agent.owner_id is None or agent.owner_id != owner_id:
                return None

        return agent

    def load_definition(self, agent_id: str):

        file_path = (
            self.storage_path /
            f"{agent_id}.AGENT.md"
        )

        if not file_path.exists():
            return None

        return file_path.read_text(
            encoding="utf-8"
        )

    def list_agents(self, owner_id: str | None = None):

        agents = []

        for file in self.storage_path.glob("*.json"):

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)
                agent = Agent(**data)

                if owner_id is not None:
                    if agent.owner_id is None or agent.owner_id != owner_id:
                        continue

                agents.append(agent)

        return agents

    def delete(self, agent_id: str, owner_id: str | None = None):

        file_path = (
            self.storage_path /
            f"{agent_id}.json"
        )

        if not file_path.exists():
            return False

        if owner_id is not None:
            agent = self.get(agent_id)
            if agent is None or agent.owner_id != owner_id:
                return False

        file_path.unlink()

        return True

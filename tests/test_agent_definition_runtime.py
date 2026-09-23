import asyncio
from pathlib import Path

from app import main
from app.agents.model import Agent
from app.agents.registry import AgentRegistry


def make_agent():
    return Agent(
        name="Test Agent",
        goal="Resolve requests",
        id="test-agent",
        description="Support",
        configuration={
            "agentType": "customer-support",
            "purpose": "Help users",
            "systemInstructions": "Be useful.",
            "personality": "friendly",
            "tone": "warm",
            "conversationStyle": "concise",
            "allowedTopics": ["billing"],
            "restrictedTopics": ["secrets"],
            "escalationRules": "Escalate disputes",
            "humanHandoffConditions": "User asks for a person",
            "llmProvider": "fake",
        },
    )


def test_runtime_configuration_renders_from_agent_without_file(monkeypatch, tmp_path):
    registry = AgentRegistry()
    registry.storage_path = Path(tmp_path)
    monkeypatch.setattr(
        registry,
        "load_definition",
        lambda agent_id: (_ for _ in ()).throw(AssertionError("file was read")),
    )
    monkeypatch.setattr(main, "agent_registry", registry)

    configuration = main.runtime_configuration(make_agent())

    assert "# Test Agent" in configuration["agent_definition"]
    assert "Escalation rules: Escalate disputes" in configuration["agent_definition"]
    assert not (Path(tmp_path) / "test-agent.AGENT.md").exists()


class FakeLLM:
    def __init__(self):
        self.configuration = None

    def configure(self, configuration):
        self.configuration = configuration

    async def stream(self, prompt, context):
        yield "response"


class FakeFactory:
    def __init__(self, llm):
        self.llm = llm

    def create_llm(self, provider_id):
        return self.llm


class FakeRegistry:
    def __init__(self, agent):
        self.agent = agent

    def get(self, agent_id):
        return self.agent

    def render_definition(self, agent):
        return AgentRegistry.render_definition(self, agent)


def test_chat_passes_generated_definition_to_llm(monkeypatch):
    agent = make_agent()
    llm = FakeLLM()
    monkeypatch.setattr(main, "agent_registry", FakeRegistry(agent))
    monkeypatch.setattr(main, "factory", FakeFactory(llm))

    response = asyncio.run(main.chat(main.ChatRequest(agent_id=agent.id, message="Hi")))

    assert response["response"] == "response"
    assert "# Test Agent" in llm.configuration["agent_definition"]


class FakeRuntime:
    def __init__(self):
        self.configuration = None
        self.started = False

    def configure(self, **kwargs):
        self.configuration = kwargs

    async def start(self):
        self.started = True


def test_start_configures_voice_runtime_with_generated_definition(monkeypatch):
    agent = make_agent()
    llm = FakeLLM()
    runtime = FakeRuntime()
    monkeypatch.setattr(main, "agent_registry", FakeRegistry(agent))
    monkeypatch.setattr(main, "factory", FakeFactory(llm))
    monkeypatch.setattr(main, "runtime", runtime)
    monkeypatch.setattr(main.rate_limiter, "check_and_record", lambda **kwargs: None)
    monkeypatch.setattr(main.memory, "configure", lambda **kwargs: None)
    monkeypatch.setattr(main, "stt", object())
    monkeypatch.setattr(main, "tts", object())

    response = asyncio.run(main.start(main.StartRequest(agent_id=agent.id, user_id="user-1")))

    assert response["status"] == "started"
    assert runtime.started is True
    assert "# Test Agent" in llm.configuration["agent_definition"]
    assert runtime.configuration["agent"] is agent
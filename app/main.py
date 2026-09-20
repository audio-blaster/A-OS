import json
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from app.providers import registry
from app.providers.factory import ProviderFactory
from app.websocket_manager import manager
from app.agent_runtime import AgentOSRuntime
from app.agents.model import Agent
from app.agents.registry import AgentRegistry
from app.conversation.state import AssistantState
from app.audio.engine import AudioEngine
from app.llm.service import LLMService
from app.tts.service import TTSService
from app.memory.service import MemoryService
from app.knowledge.service import knowledge_service
from app.security import RateLimiter, RateLimitExceeded, SpamDetected, TemporarilyBlocked

app = FastAPI(title="AgentOS")
agent_registry = AgentRegistry()
VALID_AGENT_STATUSES = {"DRAFT", "TESTING", "PUBLISHED"}


class AgentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    goal: str = ""


class AgentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = Field(default=None, min_length=1)
    goal: str | None = None


class StartRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    user_id: str | None = None


class ChatRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class PromptGeneratorRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    mode: str = Field(pattern="^(generate|improve)$")
    configuration: dict = Field(default_factory=dict)


class PromptGeneratorResponse(BaseModel):
    purpose: str
    systemInstructions: str
    goals: str
    allowedTopics: list[str] = Field(default_factory=list)
    restrictedTopics: list[str] = Field(default_factory=list)
    escalationRules: str = ""
    humanHandoffConditions: str = ""
    suggestions: list[str] = Field(default_factory=list)


def agent_response(agent: Agent):
    data = {
        **agent.configuration,
        "id": agent.id,
        "name": agent.name,
        "goal": agent.goal,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "knowledge_sources": agent.knowledge_sources,
        "channels": agent.channels,
        "status": agent.status,
        "version": agent.version,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
    }

    return data


def request_configuration(payload: BaseModel):
    return payload.model_dump(exclude_unset=True)


def normalized_status(value):
    normalized = str(value).upper()
    if normalized not in VALID_AGENT_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid agent status")
    return normalized


def runtime_configuration(agent: Agent):
    agent_definition = agent_registry.load_definition(agent.id)
    system_instructions = agent.configuration.get("systemInstructions", "")
    conversation_behavior = (
        "Stay engaged with the current exchange and trust its context. Answer the "
        "immediate point without restating or paraphrasing what is already clear. "
        "Interpret short, incomplete, or imperfect input from the conversation; if "
        "clarification is genuinely needed, ask one short question about the next "
        "useful detail, not a list of possibilities. When several details are needed, "
        "ask for only the single most useful next detail, use each answer immediately, "
        "and do not turn the conversation into a checklist or repeat what is already "
        "known. Say about as much as a natural person would need in that moment. Use "
        "plain spoken language and stop when the point is answered. Do not add habitual "
        "acknowledgements, greetings, customer-service framing, explanations of "
        "uncertainty, offers of help, or extra questions. Keep this behavior consistent "
        "with the configured agent type, personality, tone, and conversation style."
    )

    return {
        **agent.configuration,
        "agent_id": agent.id,
        "agent_definition": "\n\n".join(
            part for part in (
                agent_definition,
                system_instructions,
                conversation_behavior,
            ) if part
        ),
        "name": agent.name,
        "goal": agent.goal,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "knowledge_sources": agent.knowledge_sources,
        "channels": agent.channels,
    }


def configured_llm(agent: Agent, configuration=None):
    configuration = configuration or runtime_configuration(agent)
    selected_llm = factory.create_llm(
        configuration.get("llmProvider", "perplexity")
    )
    if hasattr(selected_llm, "configure"):
        selected_llm.configure(configuration)
    return selected_llm, configuration

# -----------------------------
# Services
# -----------------------------
factory = ProviderFactory(registry)
audio_engine = AudioEngine()
stt = factory.create_stt("sarvam")
llm = factory.create_llm("perplexity")
tts = factory.create_tts("sarvam")
memory = MemoryService()

# Rate limiting configuration
rate_limiter = RateLimiter(
    max_requests_per_window=5,        # Max 5 conversation starts
    window_seconds=60,                # Per 60 seconds
    spam_threshold=3,                 # 3 identical requests
    spam_window_seconds=30,           # In 30 seconds = spam
    block_duration_seconds=300,       # Block for 5 minutes
)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Global state
# -----------------------------
assistant_state = "idle"

async def set_state(state: AssistantState):
    global assistant_state

    if isinstance(state, AssistantState):
        assistant_state = state.value
    else:
        assistant_state = state

    await manager.broadcast(
        "state",
        {"value": assistant_state}
    )

# -----------------------------
# Runtime (NOW set_state exists)
# -----------------------------
runtime = AgentOSRuntime(
    audio_engine=audio_engine,
    stt=stt,
    llm=llm,
    tts=tts,
    memory=memory,
    manager=manager,
    set_state=set_state,
)
audio_engine.set_browser_audio_callback(manager.broadcast_audio)

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {"message": "AgentOS Backend is Running"}

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/providers")
async def providers():
    return {
        "stt": [
            {
                "id": provider_id,
                "name": provider.name,
                "models": ["saaras:v3"] if provider_id == "sarvam" else [],
                "voices": [],
            }
            for provider_id, provider in registry.stt.items()
        ],
        "llm": [
            {
                "id": provider_id,
                "name": provider.name,
                "models": getattr(
                    provider,
                    "models",
                    ["sonar"] if provider_id == "perplexity" else [],
                ),
                "voices": [],
            }
            for provider_id, provider in registry.llm.items()
        ],
        "tts": [
            {
                "id": provider_id,
                "name": provider.name,
                "models": ["bulbul:v3"] if provider_id == "sarvam" else [],
                "voices": ["rahul"] if provider_id == "sarvam" else [],
            }
            for provider_id, provider in registry.tts.items()
        ],
    }


@app.post("/agents", status_code=201)
async def create_agent(payload: AgentCreateRequest):
    configuration = request_configuration(payload)
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=422, detail="Agent name is required")

    goal = configuration.get("goal") or configuration.get("goals") or ""
    status = normalized_status(configuration.get("status", "draft"))
    agent = Agent(
        name=name,
        goal=goal,
        description=configuration.get("description", ""),
        capabilities=configuration.get("enabledTools", []),
        knowledge_sources=configuration.get("knowledgeSources", []),
        channels=configuration.get("channels", []),
        status=status,
        configuration=configuration,
    )
    agent_registry.save(agent)
    knowledge_service.reindex_agent(agent.id, agent.knowledge_sources)

    return agent_response(agent)


@app.get("/agents")
async def list_agents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=""),
    status: str | None = None,
):
    agents = agent_registry.list_agents()
    search_term = search.strip().lower()
    status_term = normalized_status(status) if status else None

    if search_term:
        agents = [
            agent for agent in agents
            if search_term in agent.name.lower()
            or search_term in agent.description.lower()
        ]

    if status_term:
        agents = [agent for agent in agents if agent.status.upper() == status_term]

    agents.sort(key=lambda agent: agent.updated_at, reverse=True)
    total = len(agents)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": [agent_response(agent) for agent in agents[start:end]],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = agent_registry.get(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent_response(agent)


@app.patch("/agents/{agent_id}")
async def update_agent(agent_id: str, payload: AgentUpdateRequest):
    agent = agent_registry.get(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    updates = request_configuration(payload)
    if "name" in updates:
        updates["name"] = updates["name"].strip()
        if not updates["name"]:
            raise HTTPException(status_code=422, detail="Agent name is required")

    agent.configuration.update(updates)
    agent.name = updates.get("name", agent.name)
    agent.goal = updates.get("goal", updates.get("goals", agent.goal))
    agent.description = updates.get("description", agent.description)
    agent.capabilities = updates.get("enabledTools", agent.capabilities)
    agent.knowledge_sources = updates.get("knowledgeSources", agent.knowledge_sources)
    agent.channels = updates.get("channels", agent.channels)
    agent.status = normalized_status(updates.get("status", agent.status))
    agent.updated_at = datetime.utcnow().isoformat()
    agent_registry.save(agent)
    knowledge_service.reindex_agent(agent.id, agent.knowledge_sources)

    return agent_response(agent)


@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    if not agent_registry.delete(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"status": "deleted", "id": agent_id}

@app.post("/start")
async def start(payload: StartRequest):
    user_id = (payload.user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=422, detail="AOS User ID is required")

    # Check rate limiting and spam detection
    try:
        rate_limiter.check_and_record(user_id=user_id, agent_id=payload.agent_id)
    except TemporarilyBlocked as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except SpamDetected as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e)) from e

    print(f"[AUDIO] start requested agent_id={payload.agent_id} user_id={user_id}")
    agent = agent_registry.get(payload.agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    configuration = runtime_configuration(agent)
    try:
        selected_stt = factory.create_stt(configuration.get("sttProvider", "sarvam"))
        selected_llm, configuration = configured_llm(agent, configuration)
        selected_tts = factory.create_tts(configuration.get("ttsProvider", "sarvam"))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    print(
        f"[AUDIO] agent_id={agent.id} "
        f"user_id={user_id} "
        f"llm_provider={configuration.get('llmProvider', 'perplexity')} "
        f"llm_model={configuration.get('llmModel', 'sonar')}"
    )

    memory.configure(
        agent_id=agent.id,
        user_id=user_id,
        configuration=configuration,
    )

    runtime.configure(
        agent=agent,
        stt=selected_stt,
        llm=selected_llm,
        tts=selected_tts,
        user_id=user_id,
    )
    await runtime.start()

    return {
        "status": "started",
        "agent_id": agent.id,
        "user_id": memory.session.user_id,
        "session_id": memory.session.session_id,
    }


@app.post("/chat")
async def chat(payload: ChatRequest):
    print("[CHAT] received")
    print(f"[CHAT] agent_id={payload.agent_id}")
    print(f"[CHAT] message={payload.message}")

    agent = agent_registry.get(payload.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        selected_llm, configuration = configured_llm(agent)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    print(
        f"[CHAT] llm_provider={configuration.get('llmProvider', 'perplexity')} "
        f"llm_model={configuration.get('llmModel', 'sonar')}"
    )

    kb_context = knowledge_service.render_context_for_query(agent.id, payload.message, limit=3)
    context = kb_context

    response_parts = []
    async for token in selected_llm.stream(payload.message, context):
        response_parts.append(token)

    response = "".join(response_parts).strip()
    print("[CHAT] response sent")
    return {"agent_id": agent.id, "response": response}


@app.post("/prompt-generator", response_model=PromptGeneratorResponse)
async def generate_prompt(payload: PromptGeneratorRequest):
    configuration = payload.configuration
    provider_id = configuration.get("llmProvider", "perplexity")

    try:
        selected_llm = factory.create_llm(provider_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    if hasattr(selected_llm, "configure"):
        selected_llm.configure(configuration)

    request_context = {
        "agent_type": configuration.get("agentType", "custom"),
        "description": configuration.get("description", ""),
        "personality": configuration.get("personality", ""),
        "tone": configuration.get("tone", ""),
        "conversation_style": configuration.get("conversationStyle", ""),
        "purpose": configuration.get("purpose", ""),
        "system_instructions": configuration.get("systemInstructions", ""),
        "goals": configuration.get("goals", ""),
        "allowed_topics": configuration.get("allowedTopics", []),
        "restricted_topics": configuration.get("restrictedTopics", []),
        "escalation_rules": configuration.get("escalationRules", ""),
        "human_handoff_conditions": configuration.get("humanHandoffConditions", ""),
    }
    task = "Generate from scratch" if payload.mode == "generate" else "Improve the existing prompt"
    prompt = f"""
You are helping configure a voice agent. {task} for exactly these sections:
Purpose & Context, System Instructions, Goals & Success Criteria, Allowed Topics, Restricted Topics,
Escalation Rules, and Human Handoff Conditions.
Use the provided agent configuration as one coherent behavioral specification: Agent Type,
Personality, Tone, Conversational Style, Purpose, and Goals must all work together. The generated
instructions should reflect the actual role the agent is performing and sound like a capable human
fulfilling that role, without pretending to be human or inventing a fake identity.

Synthesize the configuration into a single, natural system prompt rather than a stack of separate
generic paragraphs. The chosen Agent Type should shape how the agent behaves in conversation, while
Personality and Tone adjust its attitude, and Conversational Style governs pacing and delivery.
The result should sound like a real person in that role: calm, practical, and resolution-focused when
appropriate; patient, explanatory, and understanding when the role requires teaching; encouraging but
challenging when the role is coaching; curious and conversational when the role is sales-oriented.

The generated systemInstructions should tell the agent to talk with the user directly, as someone already
engaged in the conversation, rather than performing "being conversational." Listen to what the user
actually said, answer the immediate point first, get to the point quickly, and use only as many words as
the situation needs. Keep simple answers genuinely simple and expand only when the user needs or asks for
more. Respond to context instead of restating it, avoid unnecessary framing or politeness padding, do not
explain what you are about to say, do not summarize what the user just said, and do not automatically offer
more help or ask a follow-up question. Stop naturally once the point is answered. Let the role,
personality, tone, and style determine the exact expression of this directness.

Be as concise as a natural human would be in that moment, without a rigid sentence-count rule. Prefer an
answer followed by a brief useful explanation only when needed, then stop, rather than acknowledgement,
restatement, explanation, summary, and an invitation for another question. Do not habitually use assistant-
like framing such as "Absolutely!", "Of course!", "Great question!", "I'd be happy to", "Let me explain",
"Certainly!", "I understand that", "Based on what you've shared", "Here's what I would suggest", "I hope
that helps", or "Is there anything else I can help you with?" Use such wording only when it genuinely fits
the situation, not as automatic padding. Natural conversation does not mean constant slang, fillers, short
replies, incomplete answers, fake spontaneity, fake uncertainty, forced humor, or forced warmth; remain
competent and complete when the situation requires it, and never pretend to be human.

For voice interaction, prefer natural spoken phrasing, normal sentences, conversational flow, and clarity
over formatting. Do not use Markdown, headings, bullets, numbered lists, emojis, or decorative symbols
unless the user explicitly requests a formatted response. Numbers are fine when they are genuinely useful,
but do not create essay-like or list-heavy spoken output. Avoid forced speech fillers such as "um" or "uh",
repetitive acknowledgements, and polished or over-explanatory responses that do not serve the user's need.
When relevant, use remembered context naturally without referencing internal memory systems, retrieval, or
architecture; current user statements should take precedence.

For improve mode, preserve the user's intent, do not invent policies, prices, capabilities, business
rules, hours, products, services, or facts, and mention missing information as suggestions instead.
Make the content specific to the agent's role and goals, and keep it realistic for a voice agent with
clear role boundaries, sensible escalation paths, and helpful follow-up questions only when they are
useful.

Return only valid JSON with this shape:
{{
  "purpose":"...",
  "systemInstructions":"...",
  "goals":"...",
  "allowedTopics":["..."],
  "restrictedTopics":["..."],
  "escalationRules":"...",
  "humanHandoffConditions":"...",
  "suggestions":["..."]
}}
Suggestions must be a short list of optional missing details relevant to the selected agent type.
Mode: {payload.mode}
Configuration: {request_context}
"""

    raw_response = await selected_llm.generate_structured(
        prompt,
        "",
        PromptGeneratorResponse.model_json_schema(),
    )
    print(f"Prompt Generator provider: {provider_id}")
    print(f"Prompt Generator model: {configuration.get('llmModel', '')}")
    print("Prompt Generator raw response:")
    print(raw_response)
    try:
        import json
        return PromptGeneratorResponse.model_validate(json.loads(raw_response))
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        print("Prompt Generator parse error:")
        print(f"{type(error).__name__}: {error}")
        raise HTTPException(status_code=502, detail="The LLM returned an invalid prompt result") from error

@app.post("/stop")
async def stop():
    await runtime.stop(cancel_memory_tasks=False)
    return {"status": "stopped"}

# -----------------------------
# WebSocket
# -----------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Send current state immediately
    await websocket.send_json({
        "event": "state",
        "data": {
            "value": assistant_state
        }
    })

    try:
        while True:
            message = json.loads(await websocket.receive_text())

            if message.get("event") == "playback_complete":
                generation = message.get("data", {}).get("generation")
                await runtime.handle_playback_complete(generation)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await runtime.handle_browser_disconnect()


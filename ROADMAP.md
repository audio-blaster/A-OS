# ROADMAP

This roadmap is based on the current repository structure, runtime code, migration files, tests, and project overview. It describes the project as it exists now and the work that is clearly supported by that evidence.

> FACT: what the code and docs already establish.
>
> PLAN: work that is clearly implied by the current architecture and project direction.
>
> PROPOSAL: a reasonable idea that is not yet established as part of the repo’s committed direction.

---

## Project Vision

The project is aiming to become a configurable voice-first AI agent platform with a browser-based control surface and a Python backend runtime. The core idea is that a user can define an agent, choose its behavior and provider settings, persist that agent, and then interact with it via chat or live spoken conversation.

The repository already points to that end state:

- a React frontend for login, agent management, and configuration
- a Python FastAPI backend for API routes and runtime orchestration
- a Supabase-backed persistence layer for user-owned agents
- a provider abstraction for LLM, STT, and TTS services
- a runtime that combines memory, knowledge retrieval, and voice conversation

The intended long-term purpose is not just a chatbot but a user-configurable agent workspace in which each agent has a defined role, personality, constraints, memory behavior, and provider configuration. The current architecture is centered on that model.

---

## Current Status

### Working

These areas are currently implemented and supported by the codebase.

#### Agent lifecycle and persistence

- `A-OS/app/main.py` exposes create, list, fetch, update, and delete agent routes.
- `A-OS/app/agents/model.py` defines the canonical agent domain model.
- `A-OS/app/agents/supabase_repository.py` implements Supabase-backed persistence.
- `A-OS/app/agents/registry.py` can render an `AGENT.md` definition from agent configuration.
- `A-OS/supabase/migrations/` contains the SQL schema for `public.agents`.
- `A-OS/tests/test_agent_schema_contract.py` validates schema contract expectations.

#### Frontend authentication

- `my-auth-app/src/lib/supabase.ts` creates the Supabase browser client.
- `my-auth-app/src/App.tsx` initializes session state and auth changes.
- `my-auth-app/src/components/LoginForm.tsx` implements email/password and OAuth sign-in for Google and GitHub.

#### FastAPI backend

- `A-OS/app/main.py` defines the API surface and runtime lifecycle routes.
- `A-OS/app/main.py` includes `/`, `/health`, `/providers`, `/agents`, `/start`, `/chat`, `/prompt-generator`, `/stop`, and `/ws`.
- Backend startup validates the agent schema through `validate_schema()`.

#### Voice and runtime orchestration

- `A-OS/app/agent_runtime.py` implements a conversation runtime with listening, LLM call, TTS playback, and interruption handling.
- `A-OS/app/audio/engine.py` controls playback and audio processing.
- `A-OS/app/stt/service.py` connects to Sarvam STT and processes streaming audio.
- `A-OS/app/tts/service.py` uses Piper as a local TTS path.
- `A-OS/app/providers/` defines a provider registry and factory used to select STT/LLM/TTS implementations.

#### Multi-provider support

- `A-OS/app/providers/__init__.py` registers Sarvam STT, DeepSeek, Gemini, Perplexity, Piper TTS, and Sarvam TTS.
- Provider selection is driven by configuration and used in the runtime startup flow.

#### Knowledge and memory support

- `A-OS/app/knowledge/service.py` creates a SQLite-based retrieval layer with source indexing and query-time context injection.
- `A-OS/app/memory/service.py` includes working memory, sessions, archive support, durable memory policy, and relevant-memory retrieval.

#### Existing tests

The repository includes tests for:

- agent schema contract
- agent persistence contract
- Supabase repository adapter behavior
- conversation context
- knowledge base retrieval
- long-term memory and memory phases
- session identity

These are real code-level validations, even if they do not cover every integration path.

### Partially Working

These features exist but carry known gaps or operational assumptions.

#### Authentication boundary

- The frontend authenticates with Supabase Auth.
- The backend accepts `user_id` in request payloads and checks it against `owner_id` instead of validating a JWT server-side.
- This is a real architectural gap in the current security model.

#### Supabase schema contract and migration enforcement

- The repo expects a `public.agents` table with a defined contract.
- `A-OS/app/agents/supabase_repository.py` validates schema at startup and fails with errors like `PGRST205`/`PGRST204` if the table is wrong.
- This is useful but means the project is operationally dependent on correct database state.

#### Runtime voice pipeline

- The voice pipeline is implemented end-to-end, but it depends on live external providers and microphone/speaker access.
- It includes interruption handling and timing instrumentation, but the actual runtime behavior remains environment-sensitive.

#### Provider configuration

- Provider classes are registered and selected by ID.
- But actual runtime functionality depends on environment variables and external API access.
- Missing provider keys or bad config will block features even if the code is present.

#### Memory policy implementation

- Long-term memory is present and policy-gated.
- It is not a full production memory product and is intentionally lightweight.
- The implementation is still a local, app-level memory layer rather than a larger durable service.

#### Knowledge retrieval

- The knowledge service is working as a local SQLite/FTS retrieval system.
- It is still a relatively simple lexical retrieval layer rather than a more advanced semantic or managed retrieval stack.

### Needs Verification

These are not clearly validated by the repo and should be treated as environment-dependent until checked in a real development setup.

- the exact local Supabase dashboard configuration required for OAuth and auth redirects
- whether the repo’s UI works end-to-end without additional configuration
- whether the default backend startup path is stable in a clean machine without preexisting environment state
- whether the live provider credentials and quotas are sufficient in a fresh environment
- whether the repo’s current migration SQL is the exact final source of truth for all databases using the app
- whether local or remote deployment patterns are fully supported beyond the code paths shown here

### Not Yet Implemented

These are clearly absent from the current repository evidence.

- formal RBAC or multi-tenant authorization beyond user-owned agent filtering
- a full enterprise deployment and ops stack
- a fully hardened server-side auth model with verified JWT checks
- a complete observability and monitoring layer
- a production-grade memory backend separate from local app logic
- a full managed retrieval system beyond the local knowledge implementation
- broader product-level workflows beyond agent CRUD, voice, and knowledge support

---

## Planned Features

### Feature: Agent management lifecycle maturity

Status: Planned / In Progress

Current State:
The app already supports creation, listing, retrieval, update, and deletion of agents, but the lifecycle is still tightly coupled to a user-scoped API contract and the current Supabase schema.

Target:
The project should evolve into a more robust, repeatable lifecycle where agent creation, ownership, updates, status validation, and persistence behave consistently across frontend and backend.

Remaining Work:
- tighten schema validation and migration consistency
- improve ownership checks and validation paths
- ensure data shape remains consistent across all API and repo operations
- make agent lifecycle behavior more deterministic across runtime and persistence boundaries

Dependencies:
Supabase schema, frontend/backend API contracts, and app-level validation behavior.

Risks:
A migration mismatch can break schema validation and make agent flows fail at startup.

Notes:
This is one of the clearest project-level flows already in the codebase and is therefore an obvious upgrade target.

### Feature: Secure user ownership boundary

Status: Planned

Current State:
The backend currently depends on client-supplied `user_id` values when checking access to agents and runtime actions.

Target:
The project should move toward a verified identity boundary between the frontend and backend so that agent ownership is enforced by authenticated identity, not by trusted client-supplied values.

Remaining Work:
- enforce authenticated API validation
- confirm how Supabase user identity is surfaced to the backend
- align frontend and backend auth expectations

Dependencies:
Supabase Auth configuration, backend middleware or auth enforcement, and consistent user identity flow.

Risks:
Without stricter auth, the app can still be vulnerable to incorrect client-side trust assumptions.

### Feature: Provider abstraction maturity

Status: Planned / In Progress

Current State:
The provider registry already supports LLM, STT, and TTS selection.

Target:
The provider system should become more stable and easier to operate as more modes and models are added.

Remaining Work:
- reduce provider-specific assumptions in the flow
- improve configuration validation
- document required keys and runtime dependencies more formally
- avoid runtime failures when a provider is selected without the required credentials

Dependencies:
External provider APIs, env configuration, and provider-specific SDK compatibility.

Risks:
Provider quota limits, auth failures, and API changes can disrupt runtime behavior.

### Feature: Voice-first conversation reliability

Status: Planned / In Progress

Current State:
The runtime includes a live voice orchestration path with microphone capture, STT, interruption, LLM generation, and TTS playback.

Target:
The project should continue toward a more reliable live speech loop with better state handling, lower latency, and more predictable interruption behavior.

Remaining Work:
- harden websocket and audio lifecycle behavior
- reduce state drift between user speech, assistant playback, and interrupts
- improve graceful recovery when provider calls fail

Dependencies:
Sarvam STT/TTS services, browser audio access, and stable backend runtime.

Risks:
Audio device permissions, websocket disruptions, and provider timeouts remain real operational risks.

### Feature: Memory and knowledge grounding improvements

Status: Planned

Current State:
The repository includes both a local knowledge service and a durable memory system.

Target:
The project should continue to improve grounding quality and relevance while keeping the retrieval layer predictable and bounded.

Remaining Work:
- improve memory retrieval quality and retention logic
- clarify when durable memory is enabled
- keep memory features aligned with agent ownership and session scoping

Dependencies:
Memory configuration, agent configuration, and the current runtime context model.

Risks:
If not bounded, long-term memory may become noisy or too dependent on the underlying policy model.

---

## Planned Enhancements

### Enhancement: better conversational behavior control

Current behavior:
The agent runtime uses generated configuration and system prompt assembly to shape behavior, and the prompt generator route can synthesize or improve prompts.

Desired behavior:
System instructions should remain more consistent, more role-specific, and easier to reason about across agent types.

Remaining work:
- tighten the relationship between generated prompt fields and runtime behavior
- keep model selection and configuration aligned with role definition
- improve validation of prompt-generation output before it is used in runtime

### Enhancement: smoother voice interaction

Current behavior:
The runtime captures microphone audio, transcribes it, generates a response, and speaks it back with TTS. Interruptions are handled.

Desired behavior:
The interactive speech loop should behave more predictably under user interruptions, long responses, and provider latency.

Remaining work:
- improve message lifecycle around interruptions
- reduce stale audio and stale response handling
- harden a clear state transition model between listening, thinking, and speaking

### Enhancement: stronger agent configuration quality

Current behavior:
Agents can be configured with purpose, goals, memory, knowledge, channels, and provider settings.

Desired behavior:
The configuration should be easier to validate, easier to interpret, and less dependent on ad hoc runtime assumptions.

Remaining work:
- formalize validation and defaults
- reduce hidden assumptions across API, repository, and runtime
- make runtime configuration steps easier to audit

### Enhancement: more predictable knowledge grounding

Current behavior:
Knowledge sources are indexed into SQLite and retrieved by query context.

Desired behavior:
The project should improve the quality and reliability of grounding while keeping retrieval bounded and explainable.

Remaining work:
- improve source quality checks and handling of bad or missing documents
- clarify retrieval limits and conflict rules
- improve support for source types and content extraction reliability

### Enhancement: more robust auth and ownership flow

Current behavior:
The UI fundamentally relies on Supabase Auth; the backend still trusts `user_id` in requests.

Desired behavior:
The app should move to a more explicitly verified and auditable auth model.

Remaining work:
- align frontend and backend identity flow
- confirm server-side auth checks
- make owner validation consistent with the database policy model

---

## Technical Improvements

These are realistic incremental upgrades given the current architecture.

### Improve configuration management

Problem:
The app relies on environment variables and configuration fields that are scattered across the repo and not fully centralized.

Why it matters:
It makes onboarding, debugging, and provider config harder than it needs to be.

Proposed direction:
Document env configuration more explicitly and validate required keys before runtime starts where possible.

### Improve startup validation and failure messaging

Problem:
`validate_schema()` checks for critical schema conditions, but service startup is still sensitive to missing env values and provider misconfiguration.

Why it matters:
Missing configuration currently manifests as runtime breakage rather than clean, actionable setup feedback.

Proposed direction:
Add clearer startup checks and more actionable errors for missing env values, provider keys, and schema drift.

### Improve schema consistency

Problem:
The repo contains a canonical agent schema contract and a migration reconciliation script, which is a strong sign the current schema has been reworked multiple times.

Why it matters:
Schema drift is a real operational risk for a live app.

Proposed direction:
Keep the canonical contract explicit, ensure each migration aligns with it, and avoid divergent table expectations across different environments.

### Improve service lifecycle management

Problem:
The runtime and service objects manage audio, TTS, and STT connections with several lifecycle checks and interruption paths.

Why it matters:
Connection lifecycle bugs are a common source of real runtime instability.

Proposed direction:
Standardize start/stop/interrupt flows and keep recovery paths consistent.

### Improve test coverage around integration boundaries

Problem:
The repo contains several tests for contract and memory behavior, but it is unclear how fully the live frontend/backend integration is covered.

Why it matters:
This is the area most likely to hide regressions in configuration and environment setup.

Proposed direction:
Add systematic coverage around route behavior, auth ownership, provider config, and failure paths.

---

## Known Technical Debt

### Problem: client-side user identity is trusted by the backend

Why it exists:
Routes like `/agents` and `/start` require `user_id` values and compare them to `owner_id`.

Impact:
This is not a production-grade auth boundary and should be treated as a major technical debt item.

Suggested direction:
Move to verified server-side auth and remove client-trusted identity assumptions.

### Problem: dual persistence and generated artifact model

Why it exists:
`AgentRegistry.save()` persists via the repository and also writes a generated `AGENT.md` file under `data/agents`.

Impact:
This creates multiple sources of truth unless the code consistently treats the database as authoritative.

Suggested direction:
Clarify the canonical persistence model and unify runtime artifact generation rules.

### Problem: environment-driven runtime behavior

Why it exists:
Backend features depend on env variables such as provider keys and project credentials.

Impact:
The app can look implemented while being incomplete in a clean environment.

Suggested direction:
Improve startup validation and documentation for required configuration.

### Problem: schema drift risk in Supabase

Why it exists:
The repo contains both a creation migration and a reconciliation migration for the same table.

Impact:
Schema drift is a material risk and a likely source of operational troubleshooting.

Suggested direction:
Keep migration logic strictly versioned and aligned with the canonical contract.

### Problem: old compatibility assumptions in runtime paths

Why it exists:
The runtime has compatibility handling (`AttributeError` checks, legacy compatibility notes, and manual interrupt logic).

Impact:
This suggests evolving runtime code paths and potential transitional behavior still in place.

Suggested direction:
Reduce compatibility branches over time and consolidate on the current runtime contract.

### Problem: heavy provider and voice dependency stack

Why it exists:
The backend includes many audio and provider dependencies, including ONNX, PyAudio, Sarvam, and local TTS.

Impact:
This raises installation and maintenance complexity.

Suggested direction:
Keep the setup documentation clear and continue to isolate provider-specific failures from general app startup.

---

## Open Issues and Outstanding Problems

| Issue Area | Current Behavior | Impact | Next Action |
|---|---|---|---|
| Authentication | Backend trusts `user_id` supplied from the client | Security and ownership risk | Move to server-side auth verification |
| Supabase schema | Startup validates `public.agents` table and fails on drift | App is only usable when schema matches exactly | Keep migrations aligned and validate them before runtime |
| Provider config | Runtime depends on env variables and external API keys | Features fail silently or at runtime without clear setup feedback | Validate provider configuration earlier and more clearly |
| Voice lifecycle | STT/TTS playback and interruption paths are active but environment-sensitive | User-facing voice reliability issues | Stabilize audio lifecycle and error recovery |
| Memory policy | Durable memory is implemented but restricted to policy settings | Long-term memory can be difficult to reason about without config | Improve policy validation and documentation |
| Knowledge retrieval | Local retrieval is implemented but lightweight | Retrieval quality is bounded by the current approach | Evaluate retrieval quality and source handling |
| Frontend/backend auth alignment | Frontend uses Supabase Auth; backend uses app-level `user_id` checks | The auth model is not fully aligned | Unify identity handling |
| Operational readiness | No repo-defined deployment or ops stack is evident | Harder to ship and monitor in production | Add operational guardrails when the app matures |

---

## Potential Refactoring

### Refactor: separate auth identity from resource ownership logic

Current situation:
Resource ownership checks are embedded in routes and rely on `user_id` inputs.

Why it may help:
This would clarify the secure boundary and make the system easier to test.

Risk:
Changing auth behavior may require coordinated frontend and backend updates.

Suggested timing:
Near-term, after the current app flow is stabilized.

### Refactor: unify canonical agent contract handling

Current situation:
The codebase has a domain model, schema migration files, repository validation, and runtime-generated files.

Why it may help:
This would reduce ambiguity about the current source of truth.

Risk:
Changing the contract can affect stored data and migrations.

Suggested timing:
Immediate to near-term if the app grows beyond the current MVP setup.

### Refactor: isolate provider failures from app startup

Current situation:
Providers are selected at runtime and can raise missing-key errors.

Why it may help:
This would make app startup and feature checks clearer and more resilient.

Risk:
This is an incremental improvement rather than a broad rewrite.

Suggested timing:
Near-term.

### Refactor: simplify runtime state transitions

Current situation:
The runtime has a robust state machine for listening/thinking/speaking, but the code remains sensitive to live interruptions and event ordering.

Why it may help:
This would make the conversation loop easier to debug and less fragile.

Risk:
State transitions are delicate in real-time audio systems.

Suggested timing:
Medium-term.

---

## Performance Improvement Opportunities

### Observed problem: voice latency is a first-class concern

Evidence:
`A-OS/app/agent_runtime.py` explicitly measures STT, LLM, TTS, and playback latencies and prints a summary.

Opportunity:
Continue optimizing the audio+LLM+TTS chain for the fastest possible first response.

Future investigation:
- minimize unnecessary blocking operations in the voice loop
- reduce stale interruptions and stale chunk processing
- keep the STT/TTS connection lifecycle efficient

### Observed problem: provider and network call latency is inherent in the design

Evidence:
The app depends on external provider APIs and streaming connections for STT/TTS and LLM.

Opportunity:
Keep critical response paths minimal and avoid adding extra database or retrieval steps inside the main live path where they are not necessary.

Future investigation:
This is a likely area for optimization but should be measured against actual runtime behavior rather than assumed.

### Probable optimization opportunity: knowledge retrieval limits

Evidence:
`A-OS/app/knowledge/service.py` retrieves a limited number of relevant context chunks and injects them at query time.

Opportunity:
Tune retrieval size and ranking to improve relevance without burdening the LLM request path.

Future investigation:
Needed once agent usage grows beyond a few local knowledge sources.

### Probable optimization opportunity: memory retrieval selection

Evidence:
`A-OS/app/memory/service.py` selects a capped number of relevant memories and ranks them based on overlap.

Opportunity:
This is already a bounded retrieval approach; further optimization should focus on quality and relevance, not simply on scale.

Future investigation:
Likely medium-term work once memory usage becomes more active.

---

## Security Improvement Opportunities

### Already implemented security controls

- Frontend uses Supabase Auth for browser login.
- `public.agents` row-level security policies are created in the migration SQL.
- `owner_id` is included as part of the agent ownership concept.
- The backend validates that a requested agent belongs to the current `owner_id` before CRUD operations.

### Future improvements

#### Stronger backend auth

Current state:
The backend relies on a provided `user_id` rather than verified authentication tokens.

Future improvement:
Use server-side auth validation so the app can trust identity from the backend, not from the client.

#### Clear separation of secret and public keys

Current state:
The frontend uses public browser env values; the backend uses server-side env values.

Future improvement:
Keep server-side keys fully isolated and avoid cross-environment leakage.

#### Better secret handling and runtime validation

Current state:
The project expects API keys from provider env vars, but the repo does not define a strong central validation layer.

Future improvement:
Validate provider configuration before entering conversational or runtime flows.

#### Safer logging and diagnostics

Current state:
The code prints provider and runtime details in logs, which is useful for debugging but could become noisy or sensitive.

Future improvement:
Keep debug logging useful without leaking unnecessary credentials or sensitive runtime details.

---

## Deprecated or Replacement Candidates

### Current Component: client-provided `user_id` request contract

Why it exists:
The current API routes accept `user_id` directly, and the backend compares it to `owner_id`.

Replacement / Target:
A verified auth identity from the backend and a clearer authorization model.

Migration Condition:
This should be replaced when the app moves beyond the current trust model.

### Current Component: local file artifact generation in `AgentRegistry`

Why it exists:
The registry writes agent JSON and `.AGENT.md` files in addition to persistence in Supabase.

Replacement / Target:
A single canonical durable artifact model or a clearer rule that the database is authoritative and generated files are ancillary.

Migration Condition:
This should be revisited once the persistence model stabilizes.

### Current Component: compatibility checks and transitional runtime behavior

Why it exists:
The runtime contains notes about compatibility and fallback behavior for older STT and TTS assumptions.

Replacement / Target:
A more direct and uniform runtime service contract.

Migration Condition:
This is suitable for later cleanup after current voice features are stable.

---

## Short-Term Priorities

### Immediate

These are the most relevant blocking issues for correctness and reliability.

#### Tighten auth ownership model

Why it belongs here:
The current backend auth design is not aligned with a production-grade security boundary.

#### Resolve schema drift risk

Why it belongs here:
The database contract is enforced at startup, and schema mismatches can stop the app from working.

#### Improve provider configuration validation

Why it belongs here:
The repo already shows several provider-specific env requirements; missing keys and misconfiguration are likely to disrupt usage in a new environment.

#### Harden voice runtime failure handling

Why it belongs here:
The runtime includes interruption and timeline code, but the live voice path remains sensitive to provider and device failures.

### Near-Term

These follow from the current architecture and should likely come next.

#### Clarify canonical agent persistence model

Why it belongs here:
The project has both Supabase and generated local artifacts, which can cause ambiguity over the canonical source of truth.

#### Improve onboarding and runtime validation docs

Why it belongs here:
The project is complex enough that configuration errors are likely to block new developers.

#### Improve test coverage at API and integration boundaries

Why it belongs here:
The repo has contract tests, but the most important integration risks are still operational and environment-driven.

### Later

#### Mature provider and feature expansion

Why it belongs later:
The current architecture is already broad enough; broad multi-provider and feature expansion should happen after the core flow is stable.

#### Full auth and authorization maturity

Why it belongs later:
This depends on security and identity design work and should not be treated as a small incremental fix.

---

## Medium-Term Goals

### Goal: stable agent platform foundation

Objective:
Move from a working prototype to a predictable platform foundation with clear ownership, validation, and persistence behavior.

Expected outcome:
Agents behave consistently across create, edit, list, and delete flows without ambiguous contracts.

Prerequisites:
Schema contract clarity, auth boundary improvements, and stronger app startup validation.

Major dependencies:
Supabase project health, migration discipline, and API contract alignment.

### Goal: reliable multi-provider runtime

Objective:
Make provider selection and runtime configuration reliable across LLM, STT, and TTS flows.

Expected outcome:
Developers can select a valid provider configuration and get meaningful startup errors when it is not valid.

Prerequisites:
Provider validation and env documentation.

Major dependencies:
External provider SDKs and service credentials.

### Goal: production-minded memory and knowledge architecture

Objective:
Improve long-term memory and knowledge grounding without introducing fragile retrieval behavior.

Expected outcome:
More consistent agent answers that are grounded in context and policy-driven state.

Prerequisites:
Clear memory policy semantics and bounded retrieval design.

Major dependencies:
Agent configuration and runtime memory policy.

---

## Long-Term Technical Vision

This is a long-term direction implied by the project, not an already-implemented architecture.

The mature system implied by the repo is a user-configurable AI agent platform where each agent has:

- a durable identity in a database
- a runtime configuration model that shapes behavior
- a policy for memory and knowledge grounding
- a provider selection for LLM/STT/TTS
- a user ownership model and auth boundary
- a live conversation runtime that is resilient to interruptions and timeouts

Over time, the project likely moves toward a more operationally mature platform with:

- clearer auth and ownership enforcement
- more consistent provider abstractions
- better schema governance and migration discipline
- more observable and debuggable runtime behavior
- more formal lifecycle management for memory, knowledge, and agent state
- more stable interaction between frontend configuration and backend runtime behavior

This is a technical direction, not a claim that the repo already contains all of these capabilities.

---

## Dependencies and Risks

| Dependency / Risk | Affected Area | Impact | Mitigation / Requirement |
|---|---|---|---|
| Supabase project and migrations | Persistence, auth, schema | App may fail if the schema or keys are wrong | Keep schema aligned with migration files and validate startup state |
| LLM provider credentials | LLM runtime | Agent chat and prompt generation may fail | Configure provider keys before use |
| STT/TTS provider credentials | Voice runtime | Voice mode may be unusable without provider access | Keep env setup explicit and validate voice dependencies |
| Browser microphone access | Voice runtime | Voice features depend on device permissions | Confirm browser permissions and device availability |
| CORS and local origin rules | Frontend/backend integration | Frontend may fail to call backend if origin config is wrong | Keep local URL alignment consistent |
| External API quotas and rate limits | Providers and app runtime | Feature reliability depends on external provider access | Plan for provider limits and failure handling |
| Database schema drift | Agent data lifecycle | Startup validation can fail on mismatched schema | Preserve migration discipline |
| auth/config mismatch between frontend and backend | Security, ownership | Auth enforcement can behave inconsistently | Align identity and ownership logic |
| audio and websocket lifecycle | Voice runtime | Real-time behavior can degrade under interruptions | Harden lifecycle logic and recovery paths |

---

## GitHub Issues and Discussions

No GitHub issues or discussions were discoverable from the repository documentation.

This repo does not contain issue URLs or discussion links in the checked-in project docs that can be used as an authoritative roadmap source.

---

## Potential Future Ideas

These are proposals rather than established roadmap items.

### Proposal: stronger observability layer

This would make agent turns easier to debug by exposing latencies, provider call results, and session lifecycle states in a more structured way.

Current status: Proposal only.

### Proposal: broader multi-agent orchestration

The repo already centers a single agent runtime, but a higher-level coordination model could become valuable later if the platform grows beyond single-agent workflows.

Current status: Proposal only.

### Proposal: expanded memory and retrieval quality improvements

The project could evolve toward more advanced retrieval or memory tuning once the current local architecture is stabilized.

Current status: Proposal only.

### Proposal: deployment readiness improvements

The repo suggests an application architecture that could eventually support a production deployment, but no deployment stack or operational docs are present in the checked-in files.

Current status: Proposal only.

---

## Summary

The codebase already shows a credible direction: a Python FastAPI backend plus a React frontend centered on configurable AI agents, Supabase-backed persistence, and a live voice runtime. The main roadmap themes are not speculative; they are directly supported by the repository.

The most important near-term work is to clarify:

- auth and ownership enforcement
- schema consistency and migration safety
- provider configuration validation
- runtime reliability in the live voice path

After that, the project can evolve toward a more mature agent platform with stronger security, cleaner persistence boundaries, and more robust provider/runtime orchestration.

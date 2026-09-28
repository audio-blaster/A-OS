# Setup and Installation Guide

This project is split across two directories in the current workspace:

- `A-OS/` — the Python FastAPI backend, agent runtime, Supabase integration, and voice/AI orchestration
- `my-auth-app/` — the React + Vite frontend used for authentication and agent management

These are separate repositories. There is no root-level Compose file joining them; run each repository's Compose commands from that repository directory. Frontend Docker commands are documented in `my-auth-app/README.md`.

This guide is written for a developer who is new to the project and needs the shortest path to a working local setup.

> Important: this repository does not include a checked-in `.env.example` or a single install script. The setup is based on the code and configuration currently in the repo. Where the code does not clearly define a requirement, this guide marks it as `Needs verification` instead of guessing.

---

## 1. Repository structure

The current workspace layout is:

```text
A-OS/
├── app/
│   ├── agents/
│   ├── audio/
│   ├── conversation/
│   ├── core/
│   ├── debug/
│   ├── knowledge/
│   ├── llm/
│   ├── memory/
│   ├── providers/
│   ├── runtime/
│   ├── security/
│   ├── stt/
│   ├── tts/
│   ├── vad/
│   ├── agent_runtime.py
│   ├── main.py
│   ├── websocket_manager.py
│   └── ...
├── data/
├── supabase/
│   └── migrations/
├── tests/
├── en_US-lessac-medium.onnx
├── en_US-lessac-medium.onnx.json
├── jarvis_runtime.py
├── main.py
├── PROJECT_OVERVIEW.md
├── requirements.txt
├── venv/
├── .gitignore
└── SETUP.md

my-auth-app/
├── src/
├── public/
├── index.html
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── venv/
└── node_modules/
```

### What each major directory does

- `A-OS/app/` — backend application code. This is where the FastAPI server, runtime orchestration, memory, knowledge, audio pipeline, providers, and agent logic live.
- `A-OS/data/` — local data artifacts created at runtime, including generated agent metadata and knowledge storage.
- `A-OS/supabase/migrations/` — database migration SQL files for the Supabase Postgres schema.
- `A-OS/tests/` — Python tests that validate the repository, agent schema, and memory behavior.
- `A-OS/venv/` — Python virtual environment location used in this workspace.
- `my-auth-app/src/` — frontend source code; this is where the app UI and Supabase auth client live.
- `my-auth-app/node_modules/` — frontend package installation folder (user-installed dependencies).
- `my-auth-app/venv/` — present in the workspace, but this is not the backend runtime environment; the actual app is a Node/Vite project.

### Where frontend development happens

Frontend development happens in:

```text
my-auth-app/
```

The frontend is a Vite + React + TypeScript app. Its dev server is configured in `my-auth-app/package.json` and default Vite behavior.

### Where backend development happens

Backend development happens in:

```text
A-OS/
```

The backend is a Python FastAPI app with agent runtime logic in `A-OS/app/` and API entry point in `A-OS/app/main.py`.

### Where the Python virtual environment belongs

Typical backend virtual environment:

```text
A-OS/venv/
```

The repo currently contains a `venv` directory at the backend root. Use that as the Python environment location when working locally.

### Where frontend dependencies belong

Frontend dependencies are installed under:

```text
my-auth-app/node_modules/
```

### Where migrations are located

Supabase migrations live here:

```text
A-OS/supabase/migrations/
```

### Where tests are located

Backend tests live here:

```text
A-OS/tests/
```

### Where important configuration files live

- Backend runtime config: environment variables passed to the Python process
- Frontend runtime config: environment variables used by Vite (`VITE_*`)
- Supabase schema: `A-OS/supabase/migrations/*.sql`
- Backend dependency list: `A-OS/requirements.txt`
- Frontend dependency list: `my-auth-app/package.json`

---

## 2. Supported operating systems

The repository is currently verified in a Windows workspace.

The codebase uses standard Python, Node, Vite, FastAPI, and Supabase tooling. That means the project is designed to be broadly cross-platform in principle, but the repo itself only clearly verifies the Windows environment used here.

The only definitely verified environment in this workspace is:

- Windows
- Python 3.13.14
- Node.js v24.19.0

For macOS/Linux support, the repo does not provide explicit project-level guarantees. This needs verification in the development environment.

---

## 3. Hardware requirements

The project is a conversational agent platform with audio, speech, and browser-based interaction. The hardware needs are therefore driven by runtime features:

- Microphone: required for the voice workflow
- Speakers or headphones: recommended for listening to TTS output
- Stable network connection: required for Supabase, LLM, STT/TTS providers, and browser auth
- Browser: required for the React frontend
- CPU/RAM: the repo uses local Python, TTS, STT, and ONNX runtime. No explicit minimum specification is declared in the repository.
- GPU: no project requirement is explicitly defined for a GPU.

No hard minimum hardware specification is declared in the checked-in project files.

---

## 4. Required software and versions

### Verified in this workspace

| Tool | Version found | Status |
|---|---:|---|
| Python | 3.13.14 | Verified |
| Node.js | v24.19.0 | Verified |
| npm | blocked by PowerShell policy in this environment | Needs verification |
| Git | not explicitly versioned in repo | Required for clone step |
| FastAPI | 0.139.2 | Required by `A-OS/requirements.txt` |
| React | 19.0.0 | Required by `my-auth-app/package.json` |
| Vite | 6.0.0 | Required by `my-auth-app/package.json` |
| TypeScript | 5.7.0 | Required by `my-auth-app/package.json` |

### REQUIRED

- Python 3.13.x is the version verified in this workspace.
- Node.js 24.x is the version verified in this workspace.
- Git is required to clone the repository.
- `A-OS/requirements.txt` defines the backend Python dependencies.
- `my-auth-app/package.json` defines the frontend JavaScript dependencies.
- A Supabase project is required for agent persistence and authentication.
- An LLM provider key is required for runtime generation depending on the selected provider.
- A voice provider key is required for STT/TTS features.

### OPTIONAL / RECOMMENDED

- VS Code with Python and TypeScript support
- A browser for frontend testing
- A local Supabase CLI if you want to run migrations or manage Supabase locally
- Local audio setup for microphone and speaker testing

### Version policy

The repo does not declare a strict minimum supported version for every tool beyond the actual package manifest and current installed versions. The safe approach is:

- use the current major versions already in the repo for Python and Node
- do not upgrade the project to newer versions unless you are intentionally testing compatibility

---

## 5. Runtime and language requirements

### Frontend runtime

- Frontend language: TypeScript + React
- Frontend toolchain: Vite
- Frontend package manager: npm
- Frontend auth client: Supabase JS SDK

### Backend runtime

- Backend language: Python
- Backend framework: FastAPI
- Database/auth backend: Supabase Postgres + Supabase Auth
- Runtime orchestration: Python event loop and async I/O

### Python virtual environment

The backend expects a Python virtual environment for dependency isolation. The repo contains a `venv` directory under `A-OS/`, which is consistent with a standard local setup.

### Node environment

The frontend expects a Node.js runtime with npm. The repo has a `package.json` and `package-lock.json`, so the expected front-end workflow is `npm install` followed by `npm run dev`.

### System architecture summary

```text
Frontend → Node.js + React + Vite
Backend → Python + FastAPI
Database/Auth → Supabase Postgres + Supabase Auth
Voice providers → Sarvam / Piper / LLM APIs
```

---

## 6. Package and dependency requirements

### Frontend

Directory:

```text
my-auth-app/
```

Package manager:

```bash
npm
```

Install command:

```bash
cd my-auth-app
npm install
```

This is confirmed by the package configuration in `my-auth-app/package.json` and the repo’s `package-lock.json`.

### Backend

Directory:

```text
A-OS/
```

Create a virtual environment:

Windows:

```powershell
cd A-OS
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
cd A-OS
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

This is the actual dependency manifest used by the backend. The repo does not define an alternate package manager or a Poetry/pipenv setup.

### Important note on `requirements.txt`

The backend uses a large set of Python packages, including:

- FastAPI
- Uvicorn
- Supabase client
- Sarvam SDKs
- OpenAI/AI SDKs
- ONNX runtime
- PyAudio / sound packages
- `python-dotenv`

This means the backend is not a lightweight app. It expects voice + provider + audio tooling to be installed in the Python environment.

---

## 7. Repository clone instructions

1. Clone the repository using Git.
2. Enter the repository root or the relevant project folder.
3. Identify the backend directory: `A-OS/`
4. Identify the frontend directory: `my-auth-app/`
5. Set up Python dependencies for the backend.
6. Set up Node dependencies for the frontend.
7. Configure Supabase and environment variables.
8. Apply database migrations.
9. Start the backend and frontend.

Use a repository URL that you already have access to; this repo does not declare a public GitHub URL in the code. The project does not contain a safe public clone URL to copy into a setup document.

Example pattern:

```bash
git clone <your-repo-url>
cd <repo-folder>
```

---

## 8. Step-by-step installation

### Step 1 — Clone

```bash
git clone <your-repo-url>
cd <repo-folder>
```

Expected result: you now have the project on disk and can open the backend and frontend folders.

### Step 2 — Open project

Open the workspace folder containing both directories:

```text
A-OS/
my-auth-app/
```

This project is intentionally split between backend and frontend.

### Step 3 — Set up backend

Run from the backend directory:

```bash
cd A-OS
python -m venv venv
```

Activate the environment:

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Expected result: backend Python dependencies are installed and the `venv` environment is active.

### Step 4 — Set up frontend

Run from the frontend directory:

```bash
cd my-auth-app
npm install
```

Expected result: frontend dependencies are installed under `my-auth-app/node_modules`.

### Step 5 — Configure environment variables

Before starting the app, configure environment variables for the frontend and backend.

The project uses environment variables through `os.getenv(...)` and the browser `import.meta.env` pattern.

### Step 6 — Configure Supabase

The project expects a Supabase project for:

- frontend authentication (`supabase.auth`)
- agent persistence (`public.agents` table)
- user-scoped row-level security

Supabase is the application’s durable backend store for agents, not just a local dev helper.

### Step 7 — Apply migrations

The project includes migration SQL files under:

```text
A-OS/supabase/migrations/
```

Files present:

- `20260921000000_create_agents.sql`
- `20260922000000_reconcile_agents_schema.sql`

Apply them to your Supabase project using the Supabase dashboard SQL editor or the Supabase CLI if you use one.

### Step 8 — Start backend

Run from the backend directory:

```bash
cd A-OS
source venv/bin/activate   # macOS/Linux
# or .\venv\Scripts\Activate.ps1  # Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected result: the backend should start on:

```text
http://localhost:8000
```

The app also exposes FastAPI docs at:

```text
http://localhost:8000/docs
```

### Step 9 — Start frontend

Run from the frontend directory:

```bash
cd my-auth-app
npm run dev
```

Expected result: the frontend should start on:

```text
http://localhost:5173
```

### Step 10 — Verify

Open the frontend in the browser and verify that:

- the login page loads
- the backend health endpoint responds
- the frontend can authenticate with Supabase
- agent listing loads
- database schema is valid

---

## 9. Local database / Supabase setup

### What the repo actually uses

The project uses Supabase as the durable storage and authentication layer.

From the code and migration files, the backend is designed to use:

- Supabase Auth for user identity
- Supabase Postgres for the `public.agents` table
- row-level security (RLS) policies to restrict each user to their own rows

### Cloud-hosted vs local

The repo does not include a local Supabase stack setup or local development instructions. The code expects a real Supabase project. The repository is written for a cloud-hosted Supabase project, not a dedicated local Postgres-only configuration.

### Auth usage

The frontend uses Supabase Auth in `my-auth-app/src/lib/supabase.ts` and the login/register components. It calls:

- `supabase.auth.signInWithPassword(...)`
- `supabase.auth.signUp(...)`
- `supabase.auth.signInWithOAuth(...)`

This means the frontend is designed for:

- email/password sign-in
- Google OAuth
- GitHub OAuth

### Agent database setup

The relevant table is `public.agents`.

The migration files show the current expected schema includes these fields:

- `id`
- `owner_id`
- `name`
- `goal`
- `description`
- `capabilities` (JSONB)
- `knowledge_sources` (JSONB)
- `channels` (JSONB)
- `configuration` (JSONB)
- `status`
- `version`
- `created_at`
- `updated_at`

### RLS and security model

The migration files create row-level security policies so a user can only access rows where `owner_id = auth.uid()`.

This is the intended ownership model.

### Frontend vs backend keys

This is critical:

- Frontend uses the public Supabase key in the browser.
- Backend uses a server-side Supabase key or service role key to access the database.

The frontend should never hold the backend secret key.

The backend does not validate Supabase JWTs explicitly in the API routes. Instead, it trusts `user_id` supplied from the frontend in routes like `/agents` and `/start` and enforces ownership within the app logic. This is a known architectural caveat in the current codebase.

### Supabase Dashboard configuration

At minimum, the project expects:

- a Supabase project created in the dashboard
- the `public.agents` table created with the expected schema
- row-level security enabled
- email auth and/or OAuth providers enabled depending on the chosen login flow
- redirect URLs configured for local development

The exact dashboard configuration is not stored in the repo, so it must be done in the Supabase console. This needs verification in the development environment.

---

## 10. Database migrations

### Where migrations live

```text
A-OS/supabase/migrations/
```

### Existing migration files

- `20260921000000_create_agents.sql`
- `20260922000000_reconcile_agents_schema.sql`

### Naming convention

The repo uses timestamps at the front of the file name, followed by a descriptive SQL name:

```text
YYYYMMDDHHMMSS_descriptive_name.sql
```

### Which migrations are required

The repo is clearly expecting the agent table migration and the schema reconciliation migration to be applied to the Supabase database before using the app. The `validate_schema()` startup hook calls the repository and will fail if the schema is missing required columns or permissions are wrong.

### How they are expected to be applied

The repo does not define a custom migration command. There is no `supabase` CLI config or package script for migrations in the project files. Instead, the code expects the database schema to be created in the Supabase project, typically by:

- using the Supabase SQL editor, or
- using the Supabase CLI if your environment already has it configured

This is an actual repo pattern: SQL files exist, but no project-specific migration runner is defined.

### Canonical schema at a high level

The current canonical `public.agents` table is intended to hold:

- the agent ID and owner
- name and goal
- description and metadata
- JSONB configuration (behavior and model settings)
- capability, knowledge, and channel arrays
- status and version
- timestamps

The code enforces a contract in `A-OS/app/agents/supabase_repository.py` where missing columns or permission issues raise startup errors. The repository checks for required columns and fails fast if the schema is incompatible.

### Production/live data caution

The second migration script explicitly checks for invalid ownership data, invalid statuses, and schema mismatch. It is meant to prevent partially broken live data from being used silently.

### Seed data

The repo does not contain seed SQL for production or demo data. There is no default seed script in the migration files.

---

## 11. Environment variables

The code reads environment variables using `os.getenv(...)`, browser `import.meta.env`, and `python-dotenv` in some backend modules. The repositories do not include a `.env.example`. The Docker configurations use `.env` differently depending on environment; see [Docker workflows](#docker-workflows).

### Frontend variables

Frontend file:

```text
my-auth-app/src/lib/supabase.ts
```

The code reads:

```ts
import.meta.env.VITE_SUPABASE_URL
import.meta.env.VITE_SUPABASE_ANON_KEY
```

Create a frontend environment file in the frontend folder, such as `.env`, and populate:

```env
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-public-anon-key>
```

### Backend variables

The backend repository creation code expects:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

or fallback to:

```text
SUPABASE_ANON_KEY
```

These are read here:

```text
A-OS/app/agents/supabase_repository.py
```

Example values:

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-server-secret>
# or
SUPABASE_ANON_KEY=<your-public-anon-key>
```

### LLM variables actually used by code

| Variable | Used by | Required? | Secret? | Purpose |
|---|---|---|---|---|
| `SUPABASE_URL` | backend repository | Yes | No | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | backend repository | Usually Yes for server access | Yes | Server-side read/write access |
| `SUPABASE_ANON_KEY` | backend repository fallback | Conditional | No | Public key fallback |
| `VITE_SUPABASE_URL` | frontend | Yes | No | Browser Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | frontend | Yes | No | Browser public key |
| `PERPLEXITY_API_KEY` | `A-OS/app/llm/service.py` and Perplexity provider | Required if using Perplexity | Yes | LLM access |
| `DEEPSEEK_API_KEY` | DeepSeek provider | Required if using DeepSeek | Yes | LLM access |
| `GEMINI_API_KEY` | Gemini provider | Required if using Gemini | Yes | LLM access |
| `SARVAM_API_KEY` | STT and TTS Sarvam services | Required for voice STT/TTS | Yes | Speech API access |
| `PIPER_MODEL_PATH` | `A-OS/app/tts/service.py` | Optional | No | Piper model file path |
| `PIPER_EXECUTABLE` | `A-OS/app/tts/service.py` | Optional | No | Piper binary path |

### Special environment note

The frontend and backend may point to the same Supabase project, but the frontend uses browser-facing build/runtime configuration while the backend uses server-side configuration. Do not put backend secrets in frontend configuration.

Never put backend secret keys into frontend code or frontend `.env` files.

### What breaks if env variables are missing

- Missing `SUPABASE_URL` or both supported backend keys (`SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_ANON_KEY`) → backend startup fails when creating the Supabase repository
- Missing `VITE_SUPABASE_URL` or `VITE_SUPABASE_ANON_KEY` → frontend auth fails to initialize
- Missing `PERPLEXITY_API_KEY` → the default LLM path cannot operate
- Missing `SARVAM_API_KEY` → STT/TTS voice features fail
- Missing provider API keys → provider constructors raise runtime errors

## Docker workflows

The commands below apply to the backend repository directory (`A-OS`). Frontend commands are in `my-auth-app/README.md`. Build, start, and stop the two repositories separately.

### Backend LOCAL

`docker-compose.yaml` builds the existing `Dockerfile`, publishes `8000:8000`, bind-mounts the source at `/app`, reads `.env` with service-level `env_file`, and starts Uvicorn with `--reload`.

```sh
docker compose build
docker compose up
docker compose down
```

### Backend DEV

`docker-compose.dev.yaml` builds an image with no source bind mount or reload. It reads `.env` with service-level `env_file` and declares named volumes for backend data and memory.

```sh
docker compose -f docker-compose.dev.yaml build
docker compose -f docker-compose.dev.yaml up
docker compose -f docker-compose.dev.yaml down
```

### Backend PROD

`docker-compose.prod.yaml` builds the existing `Dockerfile`, has no source bind mount or reload, and runs one Uvicorn worker. It does not use a service-level `env_file`; values are supplied for Compose interpolation.

```sh
docker compose --env-file .env -f docker-compose.prod.yaml build
docker compose --env-file .env -f docker-compose.prod.yaml up
docker compose --env-file .env -f docker-compose.prod.yaml down
```

For PROD, the referenced `.env` is the backend repository's Compose interpolation file. The checked-in DEV backend Compose file does not require Compose interpolation; it injects `.env` into the service through `env_file: .env`.

### Environment-variable mechanisms

These mechanisms are distinct:

- **Compose interpolation:** `docker compose --env-file .env ...` supplies values for `${VARIABLE}` expressions in a Compose file. Shell environment variables can also supply values and take precedence over the supplied env file.
- **Service-level `env_file`:** `env_file: .env` passes entries from that file into the running backend container. Backend LOCAL and DEV use this mechanism.
- **Vite build arguments:** Frontend DEV and PROD pass `VITE_*` values through Docker build arguments. Vite embeds these values into the generated assets at build time; they are not runtime Nginx container configuration. Frontend LOCAL runs Vite with the source tree mounted, so Vite reads its project environment directly.

### Variables used by Docker and the application

| Variable | Where used | Compose requirement / application behavior |
| --- | --- | --- |
| `VITE_SUPABASE_URL` | Frontend | Required build argument in DEV and PROD; frontend Supabase URL. |
| `VITE_SUPABASE_ANON_KEY` | Frontend | Required build argument in DEV and PROD; public browser key. |
| `VITE_API_BASE_URL` | Frontend | Required build argument in DEV and PROD; HTTP API base from which the browser derives the WebSocket URL. |
| `CORS_ORIGIN` | Backend | Required interpolation in PROD; application otherwise defaults to `http://localhost:5173`. |
| `SUPABASE_URL` | Backend | Required interpolation in PROD; required by backend repository creation. |
| `SUPABASE_ANON_KEY` | Backend | Optional interpolation in PROD; application fallback when no service-role key is set. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend application | Supported and preferred by application code over the anon key. The current PROD Compose file does not map it into the container. LOCAL/DEV service `env_file` passes entries present in their referenced file. |
| `SARVAM_API_KEY` | Backend | Required interpolation in PROD; used by the Sarvam STT/TTS services. |
| `PERPLEXITY_API_KEY` | Backend | Required interpolation in PROD; used by the default Perplexity LLM. |
| `DEEPSEEK_API_KEY` | Backend | Optional interpolation in PROD; needed if a configured agent selects DeepSeek. |
| `GEMINI_API_KEY` | Backend | Optional interpolation in PROD; needed if a configured agent selects Gemini. |
| `PIPER_MODEL_PATH`, `PIPER_EXECUTABLE` | Backend application | Optional Piper TTS settings. They are not mapped by PROD Compose; LOCAL/DEV `env_file` can pass them if present in `.env`. |

The frontend and backend port mappings and persistent mounts are:

| Environment | Frontend port / mounts | Backend port / mounts |
| --- | --- | --- |
| LOCAL | `5173`; source bind mount and `frontend_node_modules:/app/node_modules` | `8000`; source bind mount |
| DEV | `5173`; no volumes | `8000`; `aos_dev_data:/app/data`, `aos_dev_memory:/app/app/memory/storage` |
| PROD | `80`; no volumes | `8000`; `aos_prod_data:/app/data`, `aos_prod_memory:/app/app/memory/storage` |

When Compose runs on the developer's machine, the host-local URLs are:

| Environment | Frontend | Backend |
| --- | --- | --- |
| LOCAL | [http://localhost:5173](http://localhost:5173/) | [http://localhost:8000](http://localhost:8000/) |
| DEV | [http://localhost:5173](http://localhost:5173/) | [http://localhost:8000](http://localhost:8000/) |
| PROD | [http://localhost](http://localhost/) | [http://localhost:8000](http://localhost:8000/) |

Remote DEV and PROD hostnames are not defined by these repositories.

---

## 12. API keys and external services

The repo depends on several external services. These are the ones the code and configuration clearly use.

| Service | Used for | Required for startup? | Notes |
|---|---|---|---|
| Supabase | Auth + Postgres + RLS + agent persistence | Yes | Required for app data flow |
| Perplexity | LLM responses | Only if selected as LLM provider | Default LLM in code |
| DeepSeek | LLM responses | Only if selected as LLM provider | Provider exists in registry |
| Gemini | LLM responses | Only if selected as LLM provider | Provider exists in registry |
| Sarvam | STT + TTS streaming | Only for voice features | `SARVAM_API_KEY` required |
| Piper | local TTS | Only for local TTS path | Default model file is included as `en_US-lessac-medium.onnx` |

### Required for application startup

- Supabase project access for agent persistence
- At least one valid frontend env config
- At least one backend env config
- A valid OpenAI-compatible LLM path when using the default provider flow

### Required only for voice or provider-specific functionality

- `SARVAM_API_KEY` for voice workflow
- `PERPLEXITY_API_KEY` or other LLM keys depending on selected provider
- `PIPER_MODEL_PATH` if you use the local Piper speech path and do not want the default ONNX model path

---

## 13. Frontend setup

### Frontend directory

```text
my-auth-app/
```

### Frontend framework

- React
- TypeScript
- Vite

### Package manager

```bash
npm
```

### Dependency install

```bash
cd my-auth-app
npm install
```

### Frontend environment file

The frontend uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` from the browser environment. The project does not include a checked-in sample file, so you must create it in the frontend folder if your environment requires it.

Example:

```env
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-public-anon-key>
```

### Development server command

```bash
cd my-auth-app
npm run dev
```

### Default local frontend URL

```text
http://localhost:5173
```

### Supabase Auth configuration

The frontend app uses:

- `supabase.auth.getSession()`
- `supabase.auth.onAuthStateChange()`
- `supabase.auth.signInWithPassword()`
- `supabase.auth.signUp()`
- `supabase.auth.signInWithOAuth()`

The login form includes both Google and GitHub OAuth buttons. `redirectTo: window.location.origin` is passed to the OAuth call, so the local redirect domain must be allowed in Supabase Auth.

### Frontend troubleshooting

Common issues:

- missing `VITE_SUPABASE_*` values → page loads but auth fails
- wrong Supabase project URL → users cannot sign in
- browser blocked by CORS or wrong allowed origin → backend rejects requests
- wrong local redirect URL in Supabase Dashboard → OAuth fails

---

## 14. Backend setup

### Backend directory

```text
A-OS/
```

### Python version

The repo is currently verified with Python 3.13.14.

### Virtual environment setup

Windows:

```powershell
cd A-OS
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
cd A-OS
python3 -m venv venv
source venv/bin/activate
```

### Dependency installation

```bash
pip install -r requirements.txt
```

### Backend `.env` location

The repo does not define a single required `.env` path. However, the backend code reads environment variables from the process environment, and some modules call `load_dotenv()`. In practice, a root-level `.env` in `A-OS/` is the expected pattern for local development.

### Backend startup command

```bash
cd A-OS
source venv/bin/activate   # macOS/Linux
# or .\venv\Scripts\Activate.ps1  # Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Default backend URL

```text
http://localhost:8000
```

### API docs

FastAPI exposes the Swagger UI at:

```text
http://localhost:8000/docs
```

This is automatic for a FastAPI app and is consistent with the route definitions in `A-OS/app/main.py`.

### Database validation at startup

The startup hook runs:

```python
repository.validate_schema()
```

This means the backend expects the required `public.agents` table and columns to exist before it can run normally.

### Provider requirements

Backend runtime features require provider credentials depending on the agent configuration:

- `PERPLEXITY_API_KEY` for the default LLM path
- `SARVAM_API_KEY` for voice features
- `DEEPSEEK_API_KEY` or `GEMINI_API_KEY` if those providers are selected

### Successful backend startup should look like

- no startup exception from schema validation
- FastAPI app loads
- `/health` returns `{"status": "ok"}`
- `/docs` loads
- no missing environment variable exceptions

---

## 15. Authentication setup

The project uses Supabase Auth in the frontend and expects the same Supabase project to be configured for both browser auth and API data access.

### Implemented flow

- Email and password sign-in is implemented in `my-auth-app/src/components/LoginForm.tsx`
- Registration is implemented in `my-auth-app/src/components/RegisterForm.tsx`
- Google OAuth and GitHub OAuth buttons are implemented in the login view

### OAuth providers

The code explicitly references:

- Google
- GitHub

The client code uses:

```ts
supabase.auth.signInWithOAuth({
  provider,
  options: {
    redirectTo: window.location.origin,
  },
})
```

This means the actual Supabase dashboard must allow the local redirect URL, including the frontend origin used during development.

### Dashboard configuration needed

The exact list is not stored in the repo, but the project expects Supabase Auth to be configured for:

- email/password auth
- OAuth providers you want to enable
- allowed redirect URLs for local development
- correct public/frontend config values

This is the place to manage it in the Supabase Dashboard. The repo itself does not store those secrets or config values.

### Backend authentication model

The backend does not validate a JWT token at the route layer. Instead, it reads `user_id` from the request and compares it against `owner_id`.

This is a real architectural limitation of the current implementation and should be treated as a setup caveat, not a secure production-ready auth boundary.

---

## 16. How to start the application

Use two terminals.

### Terminal 1 — Backend

```bash
cd A-OS
source venv/bin/activate   # macOS/Linux
# or .\venv\Scripts\Activate.ps1  # Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 — Frontend

```bash
cd my-auth-app
npm run dev
```

### Why both processes are required

- The backend serves the API, exposes the websocket, and owns runtime orchestration.
- The frontend handles authentication, agent management, and browser-side interactions.
- The app is deliberately split into frontend and backend services.

### Local URLs

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`
- WebSocket endpoint: `ws://localhost:8000/ws`

The backend CORS config in `A-OS/app/main.py` only allows `http://localhost:5173`, so the frontend must run there unless the backend is reconfigured.

---

## 17. How to verify the installation

### Backend checks

1. Start the backend successfully.
2. Confirm `/health` returns `{"status": "ok"}`.
3. Confirm `/docs` loads in the browser.
4. Confirm the app does not fail during schema validation logic.
5. Confirm the Supabase connection is reachable and credentialed.
6. Confirm the `public.agents` table exists and has the required columns.

### Frontend checks

1. Start the frontend successfully.
2. Confirm the page loads at `http://localhost:5173`.
3. Confirm the login page appears.
4. Confirm Supabase auth works with email/password or OAuth.
5. Confirm agent listing loads after a user signs in.

### Agent flow checks

1. Create an agent.
2. Confirm it appears in the listing.
3. Edit the agent.
4. Confirm the update persists.
5. Delete the agent.
6. Confirm deletion removes it from the listing.

### Voice checks

Only perform these when the required API keys and device access are configured:

- microphone access works
- `/start` works
- STT connects and recognizes speech
- LLM responds
- TTS plays back audio
- the websocket session remains stable

These are feature-dependent and may fail if `SARVAM_API_KEY` or an LLM key is not configured.

---

## 18. Troubleshooting

### A. Python environment problems

#### Symptom: `python` is not recognized

Cause: Python is not installed or not added to `PATH`.

How to check:

```bash
python --version
```

Fix:

- install Python
- reopen the shell
- use the Python executable you installed

#### Symptom: virtual environment not activated

Cause: the terminal is not using the backend environment.

How to check:

```bash
python -c "import sys; print(sys.executable)"
```

Fix:

- activate the backend venv before running `pip install -r requirements.txt`
- verify the Python path points into `A-OS/venv`

#### Symptom: missing package or import error

Cause: dependencies are not installed or interpreter mismatch.

How to check:

```bash
pip install -r requirements.txt
```

Fix:

- use the backend venv
- confirm you are using the right interpreter

#### Symptom: module import fails during startup

Cause: wrong dependency environment or missing package installation.

How to check:

- read the traceback for the missing module
- verify `pip install -r requirements.txt` was completed

Fix:

- reinstall dependencies in the backend venv
- re-check environment variable setup

### B. Frontend problems

#### Symptom: `npm` command fails or scripts are blocked

Cause: platform-specific execution policy or shell restriction.

How to check:

```bash
npm -v
```

Fix:

- use a terminal that allows scripts
- on Windows PowerShell, execution policy may block scripts; this is environment-specific

#### Symptom: frontend cannot reach backend

Cause: backend not started, wrong host, or wrong port.

How to check:

- confirm backend is running at `http://localhost:8000`
- confirm frontend is running at `http://localhost:5173`
- check backend CORS origin

Fix:

- start backend first
- ensure frontend is pointed to the correct local origin

#### Symptom: frontend auth fails

Cause: missing or wrong `VITE_SUPABASE_*` environment values.

How to check:

- inspect the frontend env values
- verify the browser is using the same Supabase project as the backend

Fix:

- update the frontend env file
- verify the Supabase project and anon key are valid

### C. Supabase problems

#### Symptom: startup fails with missing `SUPABASE_URL` or server key

Cause: environment variables not loaded.

How to check:

- inspect the backend environment variables
- verify the project URL and key values are set in the terminal or `.env`

Fix:

- set `SUPABASE_URL`
- set `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY`

#### Symptom: wrong project or wrong key

Cause: local environment is pointing to a different Supabase project than the configured frontend.

How to check:

- compare the frontend URL/key with the backend URL/key
- verify both are from the same Supabase project or intentionally different if you are intentionally testing split config

Fix:

- align both environments to the correct project ID

#### Symptom: database table missing

Cause: migrations were not applied or the wrong database is connected.

How to check:

- confirm the `public.agents` table exists
- check `A-OS/supabase/migrations/`

Fix:

- apply the migration SQL files in the Supabase dashboard or CLI

#### Symptom: permission denied or RLS issue

Cause: the configured key does not have access or row-level security is blocking access.

How to check:

- inspect the `public.agents` policies
- look for `PGRST205`, `PGRST204`, or permission errors

Fix:

- ensure the correct project database is connected
- ensure the key has the required role and grants
- confirm `owner_id = auth.uid()` policies are in place

#### Symptom: `PGRST205`, `PGRST204`, or missing column error

Cause: the live database schema is missing required columns or mismatched types.

How to check:

- read the startup failure
- validate the table schema against the migration files

Fix:

- apply the `supabase/migrations` SQL again
- reconcile the table schema with the expected contract

### D. Agent database problems

#### Symptom: app fails on schema validation

Cause: missing columns or permission failure in `public.agents`.

How to check:

- review the backend startup failure
- compare the database table columns with the migration files

Fix:

- apply the migration scripts
- confirm your Supabase project uses the right database

#### Symptom: `permission denied for table agents`

Cause: the configured key or role does not have access to the table.

Fix:

- use a proper Supabase service-side or project key
- ensure the app is connected to the correct project

### E. Voice problems

#### Symptom: Sarvam STT/TTS call fails

Cause: `SARVAM_API_KEY` missing or invalid, or network issue.

How to check:

- confirm `SARVAM_API_KEY` is set
- confirm the backend sees it in the process environment

Fix:

- set the key and restart the backend
- ensure your network can reach the provider

#### Symptom: microphone permission or device issue

Cause: browser or OS device permissions blocked.

Fix:

- allow microphone access in the browser
- verify the local device is available

#### Symptom: backend runtime fails after start

Cause: missing LLM API key or provider configuration mismatch.

Fix:

- check `PERPLEXITY_API_KEY`, `DEEPSEEK_API_KEY`, or `GEMINI_API_KEY`
- verify the provider selected in the agent config matches the configured credentials

---

## 19. Development tools and IDE configuration

### Recommended

- VS Code
- Python extension
- TypeScript/JavaScript support
- a terminal configured for both backend and frontend work
- environment files loaded in local shell or VS Code environment

### Required

- Python runtime for backend
- Node.js + npm for frontend
- Git for cloning
- access to a Supabase project

### Useful workflow

Use separate terminals for:

- backend run
- frontend run
- debugging or logs

Use VS Code to open the `A-OS` folder and `my-auth-app` folder as part of the same workspace or as a multi-root workspace. The backend and frontend are intentionally separate project areas.

### Formatting and linting

The repo does not define a dedicated lint or formatting config in the checked-in files. There is no explicit project-level lint command in the repo. This needs verification in the development environment.

### Testing

The repo includes backend tests in `A-OS/tests/`. The tests are Python-based and can be run from the backend directory once the environment is set up.

Example pattern:

```bash
cd A-OS
source venv/bin/activate
pytest
```

This is the expected pattern based on the test folder and project configuration, but it should be checked in the actual dev environment because there is no project-specific `pytest` wrapper script in the repo.

---

## 20. Development command reference

### Backend

Create backend venv:

```bash
cd A-OS
python -m venv venv
```

Activate backend venv:

Windows:

```powershell
cd A-OS
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
cd A-OS
source venv/bin/activate
```

Install backend dependencies:

```bash
cd A-OS
pip install -r requirements.txt
```

Run backend:

```bash
cd A-OS
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Check backend health:

```bash
curl http://localhost:8000/health
```

Run backend tests:

```bash
cd A-OS
pytest
```

### Frontend

Install frontend deps:

```bash
cd my-auth-app
npm install
```

Run frontend:

```bash
cd my-auth-app
npm run dev
```

Build frontend:

```bash
cd my-auth-app
npm run build
```

Preview frontend build:

```bash
cd my-auth-app
npm run preview
```

---

## Final notes

This project is a real split-stack app. The backend is Python/FastAPI with a Supabase-backed agent store and voice orchestration; the frontend is a Vite/React app that signs users in to Supabase and manages agent workflows.

Before the app works end-to-end, you need:

1. Python backend environment
2. Node frontend environment
3. Supabase project and keys
4. required API keys for the selected AI and voice providers
5. database migrations applied to the Supabase project
6. both backend and frontend started in the correct order

If anything in this guide cannot be verified from the repo, it is marked as `Needs verification` rather than assumed.

This is the intended setup path for the current repository state.

# Asistentes Académicos — Institución Universitaria Pascual Bravo

Academic assistants backed by tool-calling agents. Students ask about their curriculum;
the agent answers by **querying the database through tools**, never by generating plausible
text. Coordination staff manage programs, courses and curricula.

A fabricated prerequisite can cause a student to enroll incorrectly. That single constraint
shapes every decision in this repository: the agent is built to abstain rather than guess,
and the interface shows which rows an answer came from.

Research line: **agents**. The measured baseline for local tool calling is in
[ADR 0006](docs/adr/0006-local-model-tool-calling-baseline.md).

---

## Quick start

```bash
py -3.13 -m virtualenv backend/.venv
```

```bash
backend/.venv/Scripts/python.exe -m pip install -e "backend[dev]"
```

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and replace `JWT_SECRET` with at least 32 random bytes. The server
starts without it, but logs a warning — a known signing key lets anyone forge a
coordination token.

```bash
docker compose up -d redis
```

The next three commands run **from `backend/`**, not from the repository root. The SQLite
path in the configuration is `./academic.db`, relative to the current working directory —
running them from elsewhere creates a second, empty database beside the real one. See
[Troubleshooting](#troubleshooting).

```bash
cd backend && ../backend/.venv/Scripts/python.exe -m alembic upgrade head
```

```bash
cd backend && SEED_COORDINATION_PASSWORD='choose-a-real-password' SEED_STUDENT_PASSWORD='choose-another-one' ../backend/.venv/Scripts/python.exe -m app.cli.seed
```

`SEED_STUDENT_PASSWORD` is optional — omit it to seed only coordination and the curriculum,
skipping the demo student. See [Credenciales de prueba](#credenciales-de-prueba) below for the
values used in local development and what the seed populates.

```bash
cd backend && ../backend/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

API documentation at <http://localhost:8000/docs>.

Tests, linting and type checking run from the **repository root** instead — see
[Commands](#commands). The split is real and is explained below.

---

## Credenciales de prueba

**Solo para desarrollo local.** Estas cuentas y contraseñas están sembradas en el `academic.db`
local vía `backend/app/cli/seed.py` (invocado con las variables de entorno de abajo — nunca
están escritas en el código). No usar estos valores fuera de una máquina de desarrollo.

| Rol | Correo | Contraseña |
|---|---|---|
| Coordinación | `coordinacion@pascualbravo.edu.co` | `Coordinacion#2026` |
| Estudiante | `jose.hernandez540@pascualbravo.edu.co` | `Estudiante#2026` |

El estudiante de prueba (Jose Hernandez) está matriculado en **Ingeniería de Software**
(código de programa `018`, SNIES 107276), semestre 5.

El seed carga la malla curricular completa del programa: **55 materias en 10 niveles, 160
créditos**, con sus prerrequisitos reales (39 relaciones). Volver a correr el seed es seguro —
las filas que ya existen se omiten, nunca se duplican.

Para regenerar estas cuentas desde cero:

```bash
cd backend && SEED_COORDINATION_PASSWORD='Coordinacion#2026' SEED_STUDENT_PASSWORD='Estudiante#2026' ../backend/.venv/Scripts/python.exe -m app.cli.seed
```

---

## Why each tool is here

Nothing in this list is here by default. The architectural decisions have their own
records under [`docs/adr/`](docs/adr/) — this table says what problem each piece solves.

| Tool | Problem it solves | Rationale |
|---|---|---|
| **FastAPI** | HTTP layer with native dependency injection, async throughout, and OpenAPI generated from the code rather than maintained beside it | — |
| **SQLAlchemy 2.0 (async)** | Typed ORM (`Mapped[...]`) that keeps persistence out of the domain layer | — |
| **Alembic** | Schema changes as reviewable migrations instead of hand-edited databases | [ADR 0004](docs/adr/0004-sqlite-first.md) |
| **SQLite + aiosqlite** | Zero infrastructure for Phase 1. PostgreSQL + pgvector arrives when a vector index is actually needed | [ADR 0004](docs/adr/0004-sqlite-first.md) |
| **Redis** | Only one inference may run at a time on 4 GB of VRAM, and uvicorn runs multiple worker processes — an in-process lock cannot see the others | [ADR 0003](docs/adr/0003-redis-inference-gate.md) |
| **Ollama** | Runs the model locally so the research question can be measured on real hardware, at zero API cost | [ADR 0006](docs/adr/0006-local-model-tool-calling-baseline.md) |
| **No agent framework** | The tool-calling loop is the object of study; `AgentExecutor` would hide exactly the mechanism being measured | [ADR 0001](docs/adr/0001-no-agent-framework.md) |
| **Pydantic v2** | Validation at the HTTP boundary, and tool JSON schemas derived from argument models so documentation cannot drift from code | — |
| **PyJWT + argon2-cffi** | Stateless authentication and password hashing that does not need a session store | — |
| **pytest + pytest-asyncio** | Async tests without ceremony; a fake `LLMProvider` makes the agent loop testable with no model running | [ADR 0001](docs/adr/0001-no-agent-framework.md) |
| **ruff** | Lint and import ordering in one fast tool, replacing flake8 + isort + black | — |
| **mypy (strict)** | Catches the contract breaks tests miss — a renamed DTO field, an Optional assigned to a non-Optional name | — |
| **Docker Compose** | Redis only. Ollama runs natively; GPU passthrough on Docker Desktop for Windows adds friction with no benefit on one machine | [ADR 0003](docs/adr/0003-redis-inference-gate.md) |

---

## Architecture

Layers at the top level, modules inside each layer. **Dependencies point inward, without
exception**, and a test enforces it rather than a convention.

```
backend/app/
├── domain/              imports nothing but the standard library
│   ├── academic/        Program, Course, CurriculumEntry, the Curriculum aggregate
│   ├── agents/          Conversation, Message, ToolCall, MessageFeedback
│   └── identity/        User, Role, StudentProfile
├── application/         imports domain only — never infrastructure or api
│   ├── academic/        commands/ (write) · queries/ (read) · ports (Protocols)
│   ├── agents/          the agent loop, tools, LLMProvider port
│   └── identity/        registration, authentication
├── infrastructure/      concrete adapters
│   ├── persistence/     SQLAlchemy models, repositories, readers, Alembic
│   └── security/        Argon2 hashing, JWT issuance
├── api/v1/              routers, Pydantic schemas, dependency wiring
├── cli/                 seed script
└── main.py
```

**Light CQRS.** Writes go through domain aggregates and enforce invariants; reads go through
a separate port and return flat DTOs. Two ports per module, one database, no event sourcing
— see [ADR 0002](docs/adr/0002-light-cqrs.md). Every agent tool is a read.

**Where the rules live.** All invariants spanning more than one curriculum entry belong to
the `Curriculum` aggregate. A command handler containing an `if` that enforces a business
rule is a defect. Details in [`docs/modules/academic.md`](docs/modules/academic.md).

**Three guards run in CI-equivalent form as ordinary tests:**

| Guard | What it prevents |
|---|---|
| `tests/architecture/test_layer_boundaries.py` | `domain` importing a framework; `application` importing `infrastructure` or `api` |
| `tests/infrastructure/test_migration_sync.py` | A model column added without an Alembic revision — invisible to every other test, fatal in production |
| `tests/docs/test_adr_structure.py` | An ADR losing its Context, Decision or Consequences section |

---

## Commands

### Which directory to run from

This trips people up, so it is stated once, plainly:

| Command | Directory | Why |
|---|---|---|
| `uvicorn`, `alembic`, `app.cli.seed` | **`backend/`** | The SQLite URL is `./academic.db`, resolved against the working directory |
| `pytest`, `ruff`, `mypy` | **repository root** | Paths are given explicitly (`backend/tests`, `backend/app`), and tests use in-memory databases |

### Run

```bash
cd backend && ../backend/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

### Tests

```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests -v
```

**Always pass the `backend/tests` path.** A bare `pytest -v` fails with async-fixture errors:
without a path argument, pytest never discovers `backend/pyproject.toml` and therefore never
reads `asyncio_mode = "auto"`.

Tests marked `llm` need a running Ollama and are excluded by default:

```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests -m llm -v
```

With coverage:

```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests --cov=app --cov-report=term-missing
```

### Lint and types

```bash
backend/.venv/Scripts/python.exe -m ruff check backend/app backend/tests backend/scripts
```

```bash
backend/.venv/Scripts/python.exe -m mypy backend/app
```

Both must be clean before a commit. `ruff check --fix` resolves import ordering
automatically.

### Database

Run from `backend/`. Verify which file you are actually touching with
`ls -la backend/academic.db` before and after — a second `academic.db` appearing at the
repository root means a command ran from the wrong directory.

```bash
cd backend && ../backend/.venv/Scripts/python.exe -m alembic upgrade head
```

```bash
cd backend && ../backend/.venv/Scripts/python.exe -m alembic revision --autogenerate -m "describe the change"
```

Alembic runs from `backend/` and uses the **synchronous** URL while the application uses the
async one — deliberate, so migrations need no async plumbing. `render_as_batch=True` is
required for SQLite and must stay in both migration functions.

### Redis

```bash
docker compose up -d redis
```

```bash
docker compose exec redis redis-cli ping
```

Persistence is disabled on purpose: Redis holds the inference gate and a response cache,
both safe to lose on restart.

### Ollama

```bash
ollama pull qwen2.5:3b
```

```bash
ollama ps
```

The `PROCESSOR` column must read `100% GPU`. Anything showing CPU means the model is
spilling into system RAM and responses will be slow.

### Measure tool-calling accuracy

```bash
backend/.venv/Scripts/python.exe backend/scripts/spike_tool_calling.py
```

Prints a tool-selection accuracy over 15 prompts. **Do not tune prompts, temperature or
tool descriptions to improve the figure** — the recorded baseline is 47%, and a tuned number
measures prompt engineering rather than the model. Any redesign is recorded as a separate
measurement. See [ADR 0006](docs/adr/0006-local-model-tool-calling-baseline.md).

---

## Deployment

Phase 1 has **no deployment target**. It runs locally on the development machine, which is
where the research measurements are taken. Before this is exposed to anyone:

- Replace `JWT_SECRET` with real random bytes. The default is an obvious placeholder and
  the server warns about it at startup.
- Migrate from SQLite to PostgreSQL — a Phase 2 requirement anyway, once embeddings need
  `pgvector`.
- Serve behind HTTPS. Tokens travel in the `Authorization` header.
- Narrow the CORS origin in `main.py`; it currently allows `http://localhost:3000` only,
  which is correct for local development and wrong for anything else.

---

## Troubleshooting

Every item here cost time at least once during development.

| Symptom | Cause and fix |
|---|---|
| `No module named venv` | The stdlib `venv` module is missing from the Python installs on this machine. Use `py -3.13 -m virtualenv backend/.venv`. |
| `ModuleNotFoundError: No module named 'app'` | The editable install was created before `backend/app/` existed, so it maps nothing. Re-run `pip install -e "backend[dev]"`. |
| 36 async-fixture errors in pytest | `pytest` was run without a path. Use `pytest backend/tests`. |
| Settings silently fall back to defaults | Fixed: `env_file` is anchored to `backend/.env` by absolute path. If you add new settings, keep it that way. |
| An empty `academic.db` appears at the repository root; migrations and data disagree | `DATABASE_URL` is `sqlite:///./academic.db`, resolved against the working directory. `uvicorn`, `alembic` and the seed CLI must all run from `backend/`. Delete the stray file and re-run from the right place. **The real fix is to anchor the database path the way `env_file` already is** — worth doing before this bites someone else. |
| Frontend tooling refuses to install | The default Node on this machine is 14.21.3. Run `nvm use 22.22.0`. |
| Chat hangs 10–30 s on the first message | Ollama is loading the model into VRAM after `keep_alive` expired. Expected; the interface has a state for it. |

---

## Where to read next

| Document | What it holds |
|---|---|
| [`docs/adr/`](docs/adr/) | Why the architecture is what it is — read before proposing a change |
| [`docs/modules/academic.md`](docs/modules/academic.md) | Curriculum rules, course name resolution, credits authority |
| [`docs/modules/identity.md`](docs/modules/identity.md) | Roles, the authentication boundary |
| [`docs/modules/agents.md`](docs/modules/agents.md) | The agent runtime contract |
| [`.claude/agents/`](.claude/agents/) | Specialised reviewers: layering, agent tools, data model, duplication, commits, quality gate |
| [`.claude/commands/`](.claude/commands/) | `/verify-layers`, `/new-tool` |

---

## Conventions

- **English** for code, comments, documentation, tests and commit messages. Interface copy
  is in Spanish — see [ADR 0005](docs/adr/0005-english-identifiers.md).
- Commits: `<type>(<scope>): <subject>`, imperative, 50 characters maximum, no trailing
  period. Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`.
- Never commit `backend/.env`, `*.db`, `backend/.venv/`, `docs/superpowers/` or
  `.superpowers/`.


Prueba:

coordinacion@pascualbravo.edu.co
tu-contraseña-de-prueba
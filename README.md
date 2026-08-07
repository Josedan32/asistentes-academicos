# Asistentes Académicos — Institución Universitaria Pascual Bravo

Academic assistants backed by tool-calling agents. Students ask about their curriculum;
the agent answers by querying the database through tools rather than generating plausible
text. Coordination manages programs, courses and curricula.

Research line: agents. See `docs/adr/` for the decisions and why they were made.

## Requirements
- Python 3.13 (`py -3.13`) and `virtualenv` (`pip install virtualenv`)
- Node 22.22.0 (`nvm use 22.22.0`)
- Docker (Redis)
- Ollama running natively with `qwen2.5:3b`

## Running the backend

    py -3.13 -m virtualenv backend/.venv
    backend/.venv/Scripts/python.exe -m pip install -e "backend[dev]"
    cp backend/.env.example backend/.env    # then set JWT_SECRET
    docker compose up -d redis
    cd backend && ../backend/.venv/Scripts/python.exe -m alembic upgrade head
    SEED_COORDINATION_PASSWORD='...' ../backend/.venv/Scripts/python.exe -m app.cli.seed
    ../backend/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

API docs at http://localhost:8000/docs

## Tests

    backend/.venv/Scripts/python.exe -m pytest backend/tests -v

Tests marked `llm` require a running Ollama and are excluded by default. Run them with
`-m llm`.

## Layout
- `backend/app/domain` — entities and rules, no framework imports (enforced by a test)
- `backend/app/application` — commands, queries, ports
- `backend/app/infrastructure` — SQLAlchemy, Redis, LLM providers, security
- `backend/app/api` — FastAPI routers
- `docs/adr` — architecture decision records
- `docs/modules` — per-module contracts

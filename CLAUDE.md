# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Orchestration

### 1. Plan Mode Default

- Enter plan mode for **ANY non-trivial task** (3+ steps or architectural decisions).
- If something goes sideways, **STOP and re-plan immediately** — don't keep pushing.
- Use plan mode for **verification steps**, not just building.
- Write **detailed specs upfront** to reduce ambiguity.

### 2. Subagent Strategy

- Use **subagents liberally** to keep the main context window clean.
- Offload **research, exploration, and parallel analysis** to subagents.
- For complex problems, **throw more compute at it via subagents**.
- **One task per subagent** for focused execution.

### 3. Self-Improvement Loop

- After **ANY correction from the user**, update `tasks/lessons.md` with the pattern.
- Write **rules for yourself that prevent the same mistake**.
- Ruthlessly **iterate on these lessons** until the mistake rate drops.
- Review lessons **at session start** for the relevant project.

### 4. Verification Before Done

- Never mark a task **complete without proving it works**.
- **Diff behavior** between main and your changes when relevant.
- Ask yourself: **"Would a staff engineer approve this?"**
- Run tests, check logs, and **demonstrate correctness**.

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask **"Is there a more elegant way?"**
- If a fix feels hacky:
  **"Knowing everything I know now, implement the elegant solution."**
- Skip this for **simple, obvious fixes** — don't over-engineer.
- **Challenge your own work** before presenting it.

### 6. Autonomous Bug Fixing

- When given a **bug report: just fix it.** Don't ask for hand-holding.
- Point at **logs, errors, failing tests** — then resolve them.
- **Zero context switching** required from the user.
- Go fix **failing CI tests** without being told how.

---

## Task Management

1. **Plan First**
   Write plan to `tasks/todo.md` with checkable items.

2. **Verify Plan**
   Check in before starting implementation.

3. **Track Progress**
   Mark items complete as you go.

4. **Explain Changes**
   Provide a high-level summary at each step.

5. **Document Results**
   Add a review section to `tasks/todo.md`.

6. **Capture Lessons**
   Update `tasks/lessons.md` after corrections.

---

## Core Principles

- **Simplicity First** — Make every change as simple as possible. Impact minimal code.
- **No Laziness** — Find root causes. No temporary fixes. Maintain senior developer standards.
- **Minimal Impact** — Changes should only touch what's necessary. Avoid introducing bugs.

---

## Project Overview

`multi-minute` is a dynamic Python script scheduler — a backend API service where users upload Python scripts, define cron schedules, manage per-script virtualenv dependencies, and monitor execution history. See `PRD.md` for the full product spec.

## Commands

```bash
# Install dependencies
cd backend && uv sync

# Run dev server
cd backend && uv run uvicorn app.main:app --reload

# Run tests
cd backend && uv run pytest

# Run a single test
cd backend && uv run pytest tests/path/to/test_file.py::test_function_name -v
```

API docs at `http://localhost:8000/docs`. Use `uv`, not `pip`, for all package operations.

---

## Architecture

### Tech Stack

- **FastAPI** — API framework
- **APScheduler 3.x** (`AsyncIOScheduler`) — cron scheduling
- **SQLModel + SQLite** — ORM and persistence (`storage/scheduler.db`)
- **Python `venv` + `subprocess`** — isolated dependency management and script execution
- **pydantic-settings** — configuration via env vars

### Three Core Entities

| Entity | Status | Description |
|---|---|---|
| `Script` | Implemented | Uploaded `.py` + optional `requirements.txt` |
| `Job` | Planned | Cron schedule mapped to a Script; `env_vars`, `cli_args`, `max_history` |
| `JobRun` | Planned | Single execution record: stdout, stderr, exit_code, timing |

### Layer Structure (`backend/app/`)

- **`models/`** — SQLModel table classes (DB schema). Only `Script` exists.
- **`schemas/`** — Pydantic response shapes, separate from models to control API exposure.
- **`repositories/`** — `AbstractScriptRepository` ABC + `SQLModelScriptRepository`. Routers always depend on the ABC, enabling mock repos in tests.
- **`routers/`** — FastAPI routers. Each injects a repo via `Depends(get_repo)`. Registered in `main.py`.
- **`services/`** — Business logic. `validator.py` (syntax check via `ast.parse`) exists; `executor.py`, `scheduler.py`, `venv_manager.py` are planned.
- **`config.py`** — `Settings` with `effective_database_url`: resolves SQLite default path or `DATABASE_URL` env override.
- **`database.py`** — engine, `get_session` generator, `create_db()` called in lifespan. Must `mkdir(parents=True, exist_ok=True)` on the db path parent or startup fails.
- **`main.py`** — FastAPI app with `lifespan` context. APScheduler start/stop hooks go here.

### Storage Layout (all `.gitignored`, all paths configurable via env vars)

```
storage/
  scripts/{script_id}/script.py        # uploaded script
  scripts/{script_id}/requirements.txt # optional deps
  venvs/{script_id}/                   # per-script virtualenv (planned)
  scheduler.db                          # SQLite database
```

### Planned Services

- **`executor.py`** — `subprocess.Popen` using `{venv}/bin/python {script_path} [cli_args]`; merges `os.environ` with job `env_vars`; captures stdout/stderr/exit code. No retry on failure.
- **`scheduler.py`** — APScheduler wrapper; loads all enabled jobs from DB on startup; updates live scheduler on Job CRUD.
- **`venv_manager.py`** — creates virtualenvs under `storage/venvs/{script_id}/`, runs `pip install -r requirements.txt` into the venv.

### Adding a New Resource (follow the Script pattern)

1. `models/{resource}.py` — SQLModel table
2. `schemas/{resource}.py` — Pydantic request/response shapes
3. `repositories/` — ABC + SQLModel implementation
4. `routers/{resource}.py` — FastAPI router with `Depends(get_repo)`
5. Register router in `main.py`

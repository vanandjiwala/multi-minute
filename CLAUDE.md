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

# Run all tests
cd backend && uv run pytest

# Run tests in a single file
cd backend && uv run pytest tests/api/test_scripts.py -v

# Run a single test
cd backend && uv run pytest tests/api/test_jobs.py::test_create_job_enabled -v

# Run only unit tests (no server required)
cd backend && uv run pytest tests/unit/ -v

# Add a dependency
cd backend && uv add <package>
cd backend && uv add --dev <package>   # dev-only
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
| `Job` | Implemented | Cron schedule mapped to a Script; `env_vars`, `cli_args`, `max_history`, `enabled` |
| `JobRun` | Planned | Single execution record: stdout, stderr, exit_code, timing |

### Layer Structure (`backend/app/`)

- **`models/`** — SQLModel table classes. `Script` and `Job` exist; `Job` uses `sa_column=Column(JSON)` for dict/list fields.
- **`schemas/`** — Pydantic request/response shapes, separate from models to control API exposure.
- **`repositories/`** — Each resource has an ABC (`base.py` / `job_base.py`) + SQLModel impl. Routers always `Depends` on the ABC, enabling mock repos in tests.
- **`routers/`** — FastAPI routers registered in `main.py`. The jobs router injects both a job repo and a script repo (to validate `script_id` on create).
- **`services/`** — `validator.py` (syntax check via `ast.parse`); `scheduler.py` (APScheduler singleton); `executor.py` and `venv_manager.py` are planned.
- **`config.py`** — `Settings` (pydantic-settings). All storage paths are env-var overridable: `STORAGE_PATH`, `DB_PATH`, `SCRIPTS_PATH`, `VENVS_PATH`, `DATABASE_URL`.
- **`database.py`** — engine, `get_session` generator, `create_db()` called in lifespan. Must `mkdir(parents=True, exist_ok=True)` on the db path parent or startup fails.
- **`main.py`** — FastAPI app with `lifespan`. On startup: creates DB tables, re-hydrates all enabled Jobs into the scheduler, then starts the scheduler. On shutdown: `scheduler.shutdown()`.

### APScheduler Singleton (`services/scheduler.py`)

`scheduler = AsyncIOScheduler()` is a **module-level singleton**. `lifespan` in `main.py` starts it once. The jobs router imports the same object and calls `schedule_job()` / `unschedule_job()` — changes are immediate (no restart needed). Job `id` (UUID) is used as the APScheduler job ID.

On restart, `lifespan` re-queries enabled jobs from the DB and re-registers them, so no schedules are lost.

`_run_job_stub` is the current callable — replace with `executor.execute_job` when `executor.py` is built.

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
- **`venv_manager.py`** — creates virtualenvs under `storage/venvs/{script_id}/`, runs `pip install -r requirements.txt` into the venv.

### Adding a New Resource (follow the Script pattern)

1. `models/{resource}.py` — SQLModel table
2. `schemas/{resource}.py` — Pydantic request/response shapes
3. `repositories/` — ABC + SQLModel implementation
4. `routers/{resource}.py` — FastAPI router with `Depends(get_repo)`
5. Register router in `main.py`

---

## Testing

Tests live in `backend/tests/`. Dev dependencies (`pytest`, `httpx`, `pytest-mock`) are already in `pyproject.toml`.

### Layout
```
tests/
  conftest.py          # shared fixtures
  unit/                # pure logic, no HTTP
  api/                 # FastAPI TestClient tests
```

### Key Fixtures (`conftest.py`)

- **`test_engine`** — in-memory SQLite with `StaticPool`; tables created/dropped per test.
- **`session`** — `Session(test_engine)`; used by repository unit tests.
- **`client`** — `TestClient(app)` with all patches applied (see below). Use for all API tests.
- **`mock_schedule_job` / `mock_unschedule_job`** — `MagicMock` patching `app.routers.jobs.schedule_job/unschedule_job`; assert call counts in job tests.
- **`make_script`** — helper that POSTs a script via `client` and returns parsed JSON; use in job tests to satisfy the `script_id` FK.

### Engine Patching Gotcha

`main.py` does `from app.database import engine`, binding the name at import time. Patching `app.database.engine` alone is not enough. The `client` fixture patches **both**:
```python
monkeypatch.setattr(db_module, "engine", test_engine)
monkeypatch.setattr(main_module, "engine", test_engine)
```
`get_session` is also overridden via `app.dependency_overrides[get_session]`.

### Scheduler in Tests

`AsyncIOScheduler.start()` requires a running event loop — it cannot be started in plain sync pytest. The `client` fixture no-ops `scheduler.start/shutdown`. Scheduler unit tests (`test_scheduler.py`) use `BackgroundScheduler` instead, which shares the same `add_job/get_job/remove_job` API.

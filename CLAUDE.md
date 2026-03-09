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

- **Simplicity First**  
  Make every change as simple as possible. Impact minimal code.

- **No Laziness**  
  Find root causes. No temporary fixes. Maintain senior developer standards.

- **Minimal Impact**  
  Changes should only touch what's necessary. Avoid introducing bugs.

## Project Overview

`multi-minute` is a dynamic Python script scheduler — a backend API service where users upload Python scripts, define cron schedules, manage per-script virtualenv dependencies, and monitor execution history. See `PRD.md` for the full product spec.

## Commands

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Run dev server
cd backend && uvicorn app.main:app --reload

# Run tests
cd backend && pytest

# Run a single test
cd backend && pytest tests/path/to/test_file.py::test_function_name -v
```

API docs available at `http://localhost:8000/docs` once the server is running.

## Architecture

### Tech Stack

- **FastAPI** — API framework
- **APScheduler 3.x** (`AsyncIOScheduler`) — cron scheduling
- **SQLModel + SQLite** — ORM and persistence (`storage/scheduler.db`)
- **Python `venv` + `subprocess`** — isolated dependency management and script execution

### Core Entities

- **Script** — uploaded `.py` file with optional `requirements.txt`
- **Job** — maps a cron schedule to a Script with optional `env_vars`, `cli_args`, `max_history`
- **JobRun** — a single execution record: stdout, stderr, exit_code, timing

### Key Services (`backend/app/services/`)

- **`executor.py`** — runs scripts via `subprocess.Popen` using the script's dedicated venv Python interpreter; captures stdout/stderr/exit code
- **`scheduler.py`** — APScheduler wrapper; loads all enabled jobs on startup, dynamically adds/removes entries on job CRUD
- **`venv_manager.py`** — creates virtualenvs under `storage/venvs/{script_id}/`, runs `pip install -r requirements.txt`
- **`validator.py`** — two-step validation: `ast.parse` syntax check, then subprocess dry run with 5s timeout

### Storage Layout

All paths are configurable via environment variables; defaults:

- `storage/scripts/` — uploaded script files
- `storage/venvs/{script_id}/` — per-script virtualenvs
- `storage/scheduler.db` — SQLite database

The `storage/` directory is `.gitignored`.

### Scheduler Lifecycle

The APScheduler `AsyncIOScheduler` is started/stopped in FastAPI's `lifespan` context (in `app/main.py`). On startup, all enabled jobs are loaded from the DB and registered. Job create/update/delete operations must also update the live scheduler.

### Execution Model

Each script runs as a subprocess using the script's venv interpreter: `{venv_path}/bin/python {script_path} [cli_args]`. The subprocess inherits `os.environ` merged with job-level `env_vars`. No retry on failure for POC.

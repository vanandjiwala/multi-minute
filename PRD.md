# multi-minute — Dynamic Python Script Scheduler

## Summary

A backend API service that allows users to upload Python scripts, define cron schedules, manage per-script dependencies, and monitor execution history. The POC focuses entirely on the API and job execution layer; a UI can be layered on later.

---

## Core Entities

| Entity | Description |
|---|---|
| `Script` | An uploaded `.py` file with optional `requirements.txt` |
| `Job` | A cron definition that maps a schedule to a Script with optional runtime params |
| `JobRun` | A single execution instance of a Job — records outcome, logs, timing |

---

## Functional Requirements

### 1. Script Management

- **Upload**: `POST /scripts` — multipart/form-data with `.py` file and optional `requirements.txt`
- **List**: `GET /scripts`
- **Get**: `GET /scripts/{id}`
- **Delete**: `DELETE /scripts/{id}` — also removes associated venv
- **Validate**: `POST /scripts/{id}/validate`
  - Step 1: Syntax check (`py_compile` / `ast.parse`)
  - Step 2: Dry run — execute the script in an isolated subprocess with a short timeout (e.g. 5s), capture exit code and output

### 2. Dependency Management

- Each script can have an associated `requirements.txt`
- On upload (or on-demand via `POST /scripts/{id}/install-deps`), the system creates a dedicated virtualenv under `storage/venvs/{script_id}/`
- Packages are installed with `pip install -r requirements.txt` into that venv
- The job executor activates the script's venv before running

### 3. Job (Schedule) Management

- **Create**: `POST /jobs` — body: `{ script_id, name, cron_expression, enabled, env_vars, cli_args, max_history }`
- **List**: `GET /jobs`
- **Get**: `GET /jobs/{id}`
- **Update**: `PUT /jobs/{id}` — update schedule, params, enabled state
- **Delete**: `DELETE /jobs/{id}`
- **Enable/Disable**: `PATCH /jobs/{id}/enabled`
- **Manual trigger**: `POST /jobs/{id}/trigger` — runs immediately, outside schedule

### 4. Job Execution

- Execution model: **subprocess** (Python `subprocess.Popen`)
- Each run uses the script's dedicated venv Python interpreter
- Runtime parameters:
  - **env_vars**: dict merged with `os.environ` for the subprocess
  - **cli_args**: list of strings appended to the python command
- Captures: `stdout`, `stderr`, exit code, start time, end time, duration
- On failure (non-zero exit): log and continue — no retry for POC

### 5. Job History & Logs

- Each `JobRun` stores: `job_id`, `status` (success/failure), `exit_code`, `stdout`, `stderr`, `started_at`, `finished_at`, `duration_ms`
- Retention: configurable `max_history` per job (default: 100 most recent runs)
- **Get runs**: `GET /jobs/{id}/runs`
- **Get single run**: `GET /jobs/{id}/runs/{run_id}`

### 6. Scheduler

- APScheduler (AsyncIOScheduler) drives cron execution
- On startup: load all enabled jobs from DB and register them
- On job create/update/delete: dynamically add/remove/modify scheduler entries
- Designed so the scheduler backend can be swapped (Celery, RQ) behind a clean interface

---

## Non-Functional Requirements (POC)

- Single-tenant, no authentication required for POC
- SQLite for persistence (`storage/scheduler.db`)
- Scripts and venvs stored under `storage/scripts/` and `storage/venvs/`
- All paths configurable via environment variables

---

## Tech Stack

| Concern | Choice |
|---|---|
| API framework | FastAPI |
| Scheduler | APScheduler 3.x (AsyncIOScheduler) |
| ORM / DB | SQLModel + SQLite |
| Dependency isolation | Python `venv` module (stdlib) |
| Script execution | `subprocess.Popen` |
| Validation | `ast.parse` + subprocess dry run |

---

## Backend Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, lifespan (scheduler start/stop)
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # SQLModel engine + session
│   ├── models/
│   │   ├── script.py        # Script ORM model
│   │   ├── job.py           # Job ORM model
│   │   └── job_run.py       # JobRun ORM model
│   ├── routers/
│   │   ├── scripts.py       # /scripts endpoints
│   │   ├── jobs.py          # /jobs endpoints
│   │   └── runs.py          # /jobs/{id}/runs endpoints
│   ├── services/
│   │   ├── executor.py      # Subprocess execution logic
│   │   ├── scheduler.py     # APScheduler wrapper
│   │   ├── venv_manager.py  # Venv creation & pip install
│   │   └── validator.py     # Syntax check + dry run
│   └── schemas/             # Pydantic request/response schemas
├── storage/                 # .gitignored — scripts, venvs, db
├── requirements.txt
└── README.md
```

---

## API Surface

```
POST   /scripts                        Upload script + optional requirements.txt
GET    /scripts                        List all scripts
GET    /scripts/{id}                   Get script detail
DELETE /scripts/{id}                   Delete script
POST   /scripts/{id}/validate          Syntax check + dry run
POST   /scripts/{id}/install-deps      Install/reinstall dependencies

POST   /jobs                           Create job (cron + script)
GET    /jobs                           List all jobs
GET    /jobs/{id}                      Get job detail
PUT    /jobs/{id}                      Update job
DELETE /jobs/{id}                      Delete job
PATCH  /jobs/{id}/enabled              Enable/disable job
POST   /jobs/{id}/trigger              Manual trigger (run immediately)

GET    /jobs/{id}/runs                 List run history
GET    /jobs/{id}/runs/{run_id}        Get single run detail
```

---

## Out of Scope (POC)

- Authentication / authorization
- UI / dashboard
- Email/webhook notifications on failure
- Distributed execution or horizontal scaling
- Container-based isolation (Docker)

---

## Verification Plan

1. `cd backend && pip install -r requirements.txt`
2. `uvicorn app.main:app --reload`
3. Visit `http://localhost:8000/docs` — confirm all endpoints appear in OpenAPI UI
4. Upload a simple script (`hello.py` that prints "hello") via `POST /scripts`
5. Create a job pointing to that script with a cron expression
6. Manually trigger via `POST /jobs/{id}/trigger`
7. Fetch `GET /jobs/{id}/runs` and confirm stdout shows "hello"
8. Upload a script with a syntax error, call `POST /scripts/{id}/validate`, confirm 400 response with error detail

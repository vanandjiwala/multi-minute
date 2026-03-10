# multi-minute backend

## Testing

Install dev dependencies (first time only):
```bash
cd backend && uv add --dev pytest httpx pytest-mock
```

Run all tests:
```bash
cd backend && uv run pytest
```

Run a specific file:
```bash
cd backend && uv run pytest tests/api/test_scripts.py -v
```

Run a single test:
```bash
cd backend && uv run pytest tests/api/test_jobs.py::test_create_job_invalid_cron -v
```

Run unit tests only:
```bash
cd backend && uv run pytest tests/unit/ -v
```

import time
import pytest
from app.models.script import Script
from app.models.job import Job
from app.repositories.job_repository import SQLModelJobRepository
from app.repositories.script_repository import SQLModelScriptRepository


@pytest.fixture()
def script(session):
    repo = SQLModelScriptRepository(session)
    return repo.create(Script(name="s.py"))


@pytest.fixture()
def repo(session):
    return SQLModelJobRepository(session)


def _make_job(script_id: str, name: str = "job") -> Job:
    return Job(name=name, script_id=script_id, cron_expression="* * * * *")


def test_create_returns_id(repo, script):
    job = repo.create(_make_job(script.id))
    assert job.id is not None
    assert job.name == "job"


def test_get_by_id_existing(repo, script):
    job = repo.create(_make_job(script.id))
    found = repo.get_by_id(job.id)
    assert found is not None
    assert found.id == job.id


def test_get_by_id_missing(repo):
    assert repo.get_by_id("nonexistent") is None


def test_list_all_ordered_newest_first(repo, script):
    j1 = repo.create(_make_job(script.id, "j1"))
    time.sleep(0.01)
    j2 = repo.create(_make_job(script.id, "j2"))
    jobs = repo.list_all()
    assert jobs[0].id == j2.id
    assert jobs[1].id == j1.id


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_update_persists(repo, script):
    job = repo.create(_make_job(script.id))
    job.name = "updated"
    updated = repo.update(job)
    assert updated.name == "updated"
    found = repo.get_by_id(job.id)
    assert found.name == "updated"


def test_delete_existing(repo, script):
    job = repo.create(_make_job(script.id))
    result = repo.delete(job.id)
    assert result is True
    assert repo.get_by_id(job.id) is None


def test_delete_missing(repo):
    result = repo.delete("nonexistent")
    assert result is False

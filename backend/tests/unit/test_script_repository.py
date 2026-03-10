import time
import pytest
from app.models.script import Script
from app.repositories.script_repository import SQLModelScriptRepository


@pytest.fixture()
def repo(session):
    return SQLModelScriptRepository(session)


def test_create_returns_id(repo):
    script = Script(name="test.py")
    created = repo.create(script)
    assert created.id is not None
    assert created.name == "test.py"


def test_get_by_id_existing(repo):
    script = repo.create(Script(name="a.py"))
    found = repo.get_by_id(script.id)
    assert found is not None
    assert found.id == script.id


def test_get_by_id_missing(repo):
    assert repo.get_by_id("nonexistent-id") is None


def test_list_all_ordered_newest_first(repo):
    s1 = repo.create(Script(name="first.py"))
    time.sleep(0.01)
    s2 = repo.create(Script(name="second.py"))
    scripts = repo.list_all()
    assert scripts[0].id == s2.id
    assert scripts[1].id == s1.id


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_update_persists(repo):
    script = repo.create(Script(name="old.py"))
    script.name = "new.py"
    updated = repo.update(script)
    assert updated.name == "new.py"
    found = repo.get_by_id(script.id)
    assert found.name == "new.py"


def test_delete_existing(repo):
    script = repo.create(Script(name="del.py"))
    result = repo.delete(script.id)
    assert result is True
    assert repo.get_by_id(script.id) is None


def test_delete_missing(repo):
    result = repo.delete("nonexistent-id")
    assert result is False

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine
from fastapi.testclient import TestClient

import app.database as db_module
import app.main as main_module
from app.database import get_session
from app.main import app


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def session(test_engine):
    with Session(test_engine) as s:
        yield s


@pytest.fixture()
def client(test_engine, tmp_path, mocker):
    mocker.patch.object(db_module, "engine", test_engine)
    mocker.patch.object(main_module, "engine", test_engine)
    mocker.patch("app.config.settings.scripts_path", str(tmp_path / "scripts"))
    mocker.patch.object(main_module.scheduler, "start", lambda: None)
    mocker.patch.object(main_module.scheduler, "shutdown", lambda: None)
    mocker.patch.object(main_module, "schedule_job", lambda job_id, cron: None)

    app.dependency_overrides[get_session] = lambda: (yield Session(test_engine))

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def mock_schedule_job(mocker):
    return mocker.patch("app.routers.jobs.schedule_job")


@pytest.fixture()
def mock_unschedule_job(mocker):
    return mocker.patch("app.routers.jobs.unschedule_job")


@pytest.fixture()
def make_script(client, tmp_path):
    """Helper to create a script via the API and return parsed JSON."""
    def _make(content: str = "x = 1\n", name: str = "script.py") -> dict:
        response = client.post(
            "/scripts",
            files={"script_file": (name, content.encode(), "text/x-python")},
        )
        assert response.status_code == 201
        return response.json()

    return _make

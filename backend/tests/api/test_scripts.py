from pathlib import Path
import pytest


def upload_script(client, content: str = "x = 1\n", name: str = "script.py", requirements: str | None = None):
    files = {"script_file": (name, content.encode(), "text/x-python")}
    if requirements is not None:
        files["requirements_file"] = ("requirements.txt", requirements.encode(), "text/plain")
    return client.post("/scripts", files=files)


def test_upload_script_only(client, tmp_path):
    response = upload_script(client)
    assert response.status_code == 201
    data = response.json()
    assert data["has_requirements"] is False
    assert "id" in data


def test_upload_script_creates_file_on_disk(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    response = upload_script(client, content="print('hello')\n", name="hello.py")
    assert response.status_code == 201
    script_id = response.json()["id"]
    assert (Path(scripts_path) / script_id / "script.py").exists()


def test_upload_with_requirements(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    response = upload_script(client, requirements="requests\n")
    assert response.status_code == 201
    data = response.json()
    assert data["has_requirements"] is True
    script_id = data["id"]
    assert (Path(scripts_path) / script_id / "requirements.txt").exists()


def test_list_scripts_empty(client):
    response = client.get("/scripts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_scripts_newest_first(client):
    upload_script(client, name="first.py")
    upload_script(client, name="second.py")
    response = client.get("/scripts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "second.py"
    assert data[1]["name"] == "first.py"


def test_get_script_found(client):
    created = upload_script(client).json()
    response = client.get(f"/scripts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_script_missing(client):
    response = client.get("/scripts/nonexistent")
    assert response.status_code == 404


def test_update_script(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    created = upload_script(client).json()
    script_id = created["id"]
    response = client.put(
        f"/scripts/{script_id}",
        files={"script_file": ("updated.py", b"y = 2\n", "text/x-python")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated.py"
    assert (Path(scripts_path) / script_id / "script.py").read_text() == "y = 2\n"


def test_update_script_missing(client):
    response = client.put(
        "/scripts/nonexistent",
        files={"script_file": ("x.py", b"x=1", "text/x-python")},
    )
    assert response.status_code == 404


def test_validate_valid_script(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    created = upload_script(client, content="x = 1\n").json()
    response = client.post(f"/scripts/{created['id']}/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["syntax_error"] is None


def test_validate_syntax_error_script(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    created = upload_script(client, content="def f(\n").json()
    response = client.post(f"/scripts/{created['id']}/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["syntax_error"] is not None


def test_validate_missing_script_id(client):
    response = client.post("/scripts/nonexistent/validate")
    assert response.status_code == 404


def test_validate_file_missing_on_disk(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    # Create script in DB, then delete file
    created = upload_script(client, content="x = 1\n").json()
    script_id = created["id"]
    (Path(scripts_path) / script_id / "script.py").unlink()
    response = client.post(f"/scripts/{script_id}/validate")
    assert response.status_code == 404


def test_delete_script(client, tmp_path, mocker):
    scripts_path = str(tmp_path / "scripts")
    mocker.patch("app.config.settings.scripts_path", scripts_path)
    mocker.patch("app.routers.scripts.settings.scripts_path", scripts_path)
    created = upload_script(client).json()
    script_id = created["id"]
    response = client.delete(f"/scripts/{script_id}")
    assert response.status_code == 204
    assert client.get(f"/scripts/{script_id}").status_code == 404
    assert not (Path(scripts_path) / script_id).exists()


def test_delete_script_missing(client):
    response = client.delete("/scripts/nonexistent")
    assert response.status_code == 404

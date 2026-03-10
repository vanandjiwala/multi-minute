import pytest


VALID_CRON = "* * * * *"
INVALID_CRON = "not a cron"


def create_job(client, script_id: str, **kwargs) -> dict:
    payload = {
        "name": "test-job",
        "script_id": script_id,
        "cron_expression": VALID_CRON,
        **kwargs,
    }
    return client.post("/jobs", json=payload)


# ---------- CREATE ----------

def test_create_job_enabled(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    response = create_job(client, script["id"], enabled=True)
    assert response.status_code == 201
    data = response.json()
    assert data["enabled"] is True
    mock_schedule_job.assert_called_once_with(data["id"], VALID_CRON)
    mock_unschedule_job.assert_not_called()


def test_create_job_disabled_no_schedule(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    response = create_job(client, script["id"], enabled=False)
    assert response.status_code == 201
    mock_schedule_job.assert_not_called()


def test_create_job_invalid_cron(client, make_script, mock_schedule_job):
    script = make_script()
    response = client.post("/jobs", json={
        "name": "bad",
        "script_id": script["id"],
        "cron_expression": INVALID_CRON,
    })
    assert response.status_code == 422
    mock_schedule_job.assert_not_called()


def test_create_job_missing_script(client, mock_schedule_job):
    response = client.post("/jobs", json={
        "name": "j",
        "script_id": "nonexistent",
        "cron_expression": VALID_CRON,
    })
    assert response.status_code == 404
    mock_schedule_job.assert_not_called()


# ---------- LIST ----------

def test_list_jobs_empty(client, mock_schedule_job, mock_unschedule_job):
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_newest_first(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    create_job(client, script["id"], name="first")
    create_job(client, script["id"], name="second")
    response = client.get("/jobs")
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "second"
    assert data[1]["name"] == "first"


# ---------- GET ----------

def test_get_job_found(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"], env_vars={"KEY": "val"}, cli_args=["--foo"]).json()
    response = client.get(f"/jobs/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["env_vars"] == {"KEY": "val"}
    assert data["cli_args"] == ["--foo"]


def test_get_job_missing(client, mock_schedule_job, mock_unschedule_job):
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 404


# ---------- UPDATE ----------

def test_update_job_name_and_cron(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"]).json()
    mock_schedule_job.reset_mock()

    new_cron = "0 * * * *"
    response = client.put(f"/jobs/{created['id']}", json={"name": "renamed", "cron_expression": new_cron})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "renamed"
    assert data["cron_expression"] == new_cron
    mock_schedule_job.assert_called_once_with(created["id"], new_cron)


def test_update_job_disable(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"], enabled=True).json()
    mock_unschedule_job.reset_mock()

    response = client.put(f"/jobs/{created['id']}", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False
    mock_unschedule_job.assert_called_once_with(created["id"])


def test_update_job_invalid_cron(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"]).json()
    mock_schedule_job.reset_mock()

    response = client.put(f"/jobs/{created['id']}", json={"cron_expression": INVALID_CRON})
    assert response.status_code == 422
    mock_schedule_job.assert_not_called()


def test_update_job_missing(client, mock_schedule_job, mock_unschedule_job):
    response = client.put("/jobs/nonexistent", json={"name": "x"})
    assert response.status_code == 404


# ---------- DELETE ----------

def test_delete_job(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"]).json()
    mock_unschedule_job.reset_mock()

    response = client.delete(f"/jobs/{created['id']}")
    assert response.status_code == 204
    mock_unschedule_job.assert_called_once_with(created["id"])
    assert client.get(f"/jobs/{created['id']}").status_code == 404


def test_delete_job_missing(client, mock_schedule_job, mock_unschedule_job):
    response = client.delete("/jobs/nonexistent")
    assert response.status_code == 404


# ---------- PATCH ENABLED ----------

def test_patch_enabled_to_false(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"], enabled=True).json()
    mock_unschedule_job.reset_mock()

    response = client.patch(f"/jobs/{created['id']}/enabled", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False
    mock_unschedule_job.assert_called_once_with(created["id"])


def test_patch_enabled_to_true(client, make_script, mock_schedule_job, mock_unschedule_job):
    script = make_script()
    created = create_job(client, script["id"], enabled=False).json()
    mock_schedule_job.reset_mock()

    response = client.patch(f"/jobs/{created['id']}/enabled", json={"enabled": True})
    assert response.status_code == 200
    assert response.json()["enabled"] is True
    mock_schedule_job.assert_called_once_with(created["id"], VALID_CRON)


def test_patch_enabled_missing(client, mock_schedule_job, mock_unschedule_job):
    response = client.patch("/jobs/nonexistent/enabled", json={"enabled": True})
    assert response.status_code == 404

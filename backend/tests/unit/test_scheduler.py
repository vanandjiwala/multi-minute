import pytest
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.scheduler import schedule_job, unschedule_job


@pytest.fixture()
def sched():
    s = BackgroundScheduler()
    s.start()
    yield s
    s.shutdown(wait=False)


def _noop(job_id: str) -> None:
    pass


def test_schedule_job_adds_new(sched, mocker):
    mocker.patch("app.services.scheduler.scheduler", sched)
    schedule_job("job-1", "* * * * *")
    assert sched.get_job("job-1") is not None


def test_schedule_job_reschedules_existing(sched, mocker):
    mocker.patch("app.services.scheduler.scheduler", sched)
    schedule_job("job-2", "* * * * *")
    schedule_job("job-2", "0 * * * *")
    jobs = [j for j in sched.get_jobs() if j.id == "job-2"]
    assert len(jobs) == 1


def test_unschedule_job_removes(sched, mocker):
    mocker.patch("app.services.scheduler.scheduler", sched)
    schedule_job("job-3", "* * * * *")
    unschedule_job("job-3")
    assert sched.get_job("job-3") is None


def test_unschedule_job_missing_no_error(sched, mocker):
    mocker.patch("app.services.scheduler.scheduler", sched)
    # Should not raise
    unschedule_job("nonexistent-job")


def test_schedule_job_invalid_cron(sched, mocker):
    mocker.patch("app.services.scheduler.scheduler", sched)
    with pytest.raises(ValueError):
        schedule_job("job-x", "not a cron")

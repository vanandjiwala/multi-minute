from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

scheduler = AsyncIOScheduler()


def _run_job_stub(job_id: str) -> None:
    """Placeholder — will be replaced by executor.execute_job in the next iteration."""
    pass


def schedule_job(job_id: str, cron_expression: str) -> None:
    """Add or reschedule a job. Safe to call whether job exists in scheduler or not."""
    trigger = CronTrigger.from_crontab(cron_expression)
    if scheduler.get_job(job_id):
        scheduler.reschedule_job(job_id, trigger=trigger)
    else:
        scheduler.add_job(_run_job_stub, trigger, id=job_id, args=[job_id])


def unschedule_job(job_id: str) -> None:
    """Remove a job. No-op if not found."""
    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        pass

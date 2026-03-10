from datetime import datetime, timezone
from typing import Annotated

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.database import get_session
from app.models.job import Job
from app.repositories.base import AbstractScriptRepository
from app.repositories.job_base import AbstractJobRepository
from app.repositories.job_repository import SQLModelJobRepository
from app.repositories.script_repository import SQLModelScriptRepository
from app.schemas.job import JobCreate, JobEnabledPatch, JobListItem, JobRead, JobUpdate
from app.services.scheduler import schedule_job, unschedule_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_repo(session: Annotated[Session, Depends(get_session)]) -> AbstractJobRepository:
    return SQLModelJobRepository(session)


def get_script_repo(session: Annotated[Session, Depends(get_session)]) -> AbstractScriptRepository:
    return SQLModelScriptRepository(session)


def _validate_cron(expression: str) -> None:
    try:
        CronTrigger.from_crontab(expression)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid cron expression: {e}")


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    job_repo: AbstractJobRepository = Depends(get_job_repo),
    script_repo: AbstractScriptRepository = Depends(get_script_repo),
):
    _validate_cron(payload.cron_expression)

    if script_repo.get_by_id(payload.script_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    job = Job(**payload.model_dump())
    job = job_repo.create(job)

    if job.enabled:
        schedule_job(job.id, job.cron_expression)

    return job


@router.get("", response_model=list[JobListItem])
def list_jobs(job_repo: AbstractJobRepository = Depends(get_job_repo)):
    return job_repo.list_all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, job_repo: AbstractJobRepository = Depends(get_job_repo)):
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: str,
    payload: JobUpdate,
    job_repo: AbstractJobRepository = Depends(get_job_repo),
):
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    updates = payload.model_dump(exclude_none=True)

    if "cron_expression" in updates:
        _validate_cron(updates["cron_expression"])

    for field, value in updates.items():
        setattr(job, field, value)
    job.updated_at = datetime.now(timezone.utc)
    job = job_repo.update(job)

    if job.enabled:
        schedule_job(job.id, job.cron_expression)
    else:
        unschedule_job(job.id)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, job_repo: AbstractJobRepository = Depends(get_job_repo)):
    deleted = job_repo.delete(job_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    unschedule_job(job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{job_id}/enabled", response_model=JobRead)
def toggle_enabled(
    job_id: str,
    payload: JobEnabledPatch,
    job_repo: AbstractJobRepository = Depends(get_job_repo),
):
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.enabled = payload.enabled
    job.updated_at = datetime.now(timezone.utc)
    job = job_repo.update(job)

    if job.enabled:
        schedule_job(job.id, job.cron_expression)
    else:
        unschedule_job(job.id)

    return job

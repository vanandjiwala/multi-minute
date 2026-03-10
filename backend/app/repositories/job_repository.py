from typing import Optional
from sqlmodel import Session, select
from app.models.job import Job
from app.repositories.job_base import AbstractJobRepository


class SQLModelJobRepository(AbstractJobRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: Job) -> Job:
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def get_by_id(self, job_id: str) -> Optional[Job]:
        return self._session.get(Job, job_id)

    def list_all(self) -> list[Job]:
        return list(self._session.exec(select(Job).order_by(Job.created_at.desc())).all())

    def update(self, job: Job) -> Job:
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def delete(self, job_id: str) -> bool:
        db_job = self._session.get(Job, job_id)
        if db_job is None:
            return False
        self._session.delete(db_job)
        self._session.commit()
        return True

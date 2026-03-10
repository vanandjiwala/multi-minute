from abc import ABC, abstractmethod
from typing import Optional
from app.models.job import Job


class AbstractJobRepository(ABC):

    @abstractmethod
    def create(self, job: Job) -> Job: ...

    @abstractmethod
    def get_by_id(self, job_id: str) -> Optional[Job]: ...

    @abstractmethod
    def list_all(self) -> list[Job]: ...

    @abstractmethod
    def update(self, job: Job) -> Job: ...

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """Returns True if deleted, False if not found."""
        ...

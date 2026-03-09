from abc import ABC, abstractmethod
from typing import Optional
from app.models.script import Script


class AbstractScriptRepository(ABC):

    @abstractmethod
    def create(self, script: Script) -> Script: ...

    @abstractmethod
    def get_by_id(self, script_id: str) -> Optional[Script]: ...

    @abstractmethod
    def list_all(self) -> list[Script]: ...

    @abstractmethod
    def update(self, script: Script) -> Script: ...

    @abstractmethod
    def delete(self, script_id: str) -> bool:
        """Returns True if deleted, False if not found."""
        ...

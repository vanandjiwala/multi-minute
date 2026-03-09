from typing import Optional
from sqlmodel import Session, select
from app.models.script import Script
from app.repositories.base import AbstractScriptRepository


class SQLModelScriptRepository(AbstractScriptRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, script: Script) -> Script:
        self._session.add(script)
        self._session.commit()
        self._session.refresh(script)
        return script

    def get_by_id(self, script_id: str) -> Optional[Script]:
        return self._session.get(Script, script_id)

    def list_all(self) -> list[Script]:
        return list(self._session.exec(select(Script).order_by(Script.created_at.desc())).all())

    def update(self, script: Script) -> Script:
        self._session.add(script)
        self._session.commit()
        self._session.refresh(script)
        return script

    def delete(self, script_id: str) -> bool:
        db_script = self._session.get(Script, script_id)
        if db_script is None:
            return False
        self._session.delete(db_script)
        self._session.commit()
        return True

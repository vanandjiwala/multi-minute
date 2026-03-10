import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    __tablename__ = "job"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    script_id: str = Field(foreign_key="script.id", index=True)
    cron_expression: str
    enabled: bool = Field(default=True)
    env_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    cli_args: list = Field(default_factory=list, sa_column=Column(JSON))
    max_history: int = Field(default=100)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

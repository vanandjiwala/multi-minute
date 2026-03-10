from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobCreate(BaseModel):
    name: str
    script_id: str
    cron_expression: str
    enabled: bool = True
    env_vars: dict[str, str] = {}
    cli_args: list[str] = []
    max_history: int = 100


class JobRead(BaseModel):
    id: str
    name: str
    script_id: str
    cron_expression: str
    enabled: bool
    env_vars: dict
    cli_args: list
    max_history: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: str
    name: str
    script_id: str
    cron_expression: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class JobUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    env_vars: Optional[dict[str, str]] = None
    cli_args: Optional[list[str]] = None
    max_history: Optional[int] = None


class JobEnabledPatch(BaseModel):
    enabled: bool

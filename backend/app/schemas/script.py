from datetime import datetime
from pydantic import BaseModel


class ScriptRead(BaseModel):
    id: str
    name: str
    has_requirements: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ScriptListItem(BaseModel):
    id: str
    name: str
    has_requirements: bool
    created_at: datetime
    model_config = {"from_attributes": True}

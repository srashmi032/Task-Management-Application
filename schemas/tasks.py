from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str

    @field_validator("priority")
    @classmethod
    def priority_must_be_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("priority must be a numeric string, e.g. '1', '2', '3'")
        return value


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def priority_must_be_numeric(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.isdigit():
            raise ValueError("priority must be a numeric string, e.g. '1', '2', '3'")
        return value

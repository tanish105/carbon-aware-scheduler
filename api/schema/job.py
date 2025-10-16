# api/schemas/job.py
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class JobCreate(BaseModel):
    name: str
    command: str
    resources: Dict[str, float]
    expected_runtime_min: int
    urgency: str
    soft_deadline: Optional[datetime] = None

class JobResponse(BaseModel):
    id: int
    name: str
    command: str
    state: str
    urgency: str
    created_at: datetime
    soft_deadline: Optional[datetime] = None

    class Config:
        orm_mode = True

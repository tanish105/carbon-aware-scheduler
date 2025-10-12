from sqlalchemy import Column, Integer, String, JSON, Enum, DateTime, Float
from sqlalchemy.sql import func
import enum

from sqlalchemy.orm import declarative_base

Base = declarative_base()

class JobState(enum.Enum):
    waiting = "waiting"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    command = Column(String, nullable=False)
    resources = Column(JSON)
    expected_runtime_min = Column(Integer)
    urgency = Column(String)
    soft_deadline = Column(DateTime)
    state = Column(Enum(JobState), default=JobState.waiting)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    carbon_savings = Column(Float, default=0.0)

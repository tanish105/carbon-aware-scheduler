# api/routes/job_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from api.db import SessionLocal
from api.models.job import Job, JobState
from api.schema.job import JobCreate, JobResponse
from celery import Celery
from datetime import datetime

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Celery producer connection (RabbitMQ)
celery_app = Celery(
    "carbon_scheduler",
    broker="amqp://guest:guest@localhost:5672//",  # adjust for your RabbitMQ
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=JobResponse)
def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    new_job = Job(
        name=job_data.name,
        command=job_data.command,
        resources=job_data.resources,
        expected_runtime_min=job_data.expected_runtime_min,
        urgency=job_data.urgency,
        soft_deadline=job_data.soft_deadline,
        state=JobState.waiting,
        created_at=datetime.utcnow(),
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Send to RabbitMQ queue (submission queue)
    celery_app.send_task("tasks.enqueue_job", args=[new_job.id])

    return new_job


@router.get("/", response_model=list[JobResponse])
def list_jobs(
    state: str | None = Query(None),
    urgency: str | None = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    if state:
        query = query.filter(Job.state == state)
    if urgency:
        query = query.filter(Job.urgency == urgency)
    return query.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel")
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.state not in [JobState.waiting, JobState.running]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    job.state = JobState.cancelled
    db.commit()
    return {"status": "cancelled", "job_id": job_id}

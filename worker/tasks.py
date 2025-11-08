# worker/tasks.py
import os
import time
from celery import Celery
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from api.db import SessionLocal
from api.models.job import Job, JobState
from dotenv import load_dotenv

app = Celery(
    "carbon_scheduler",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://"
)

app.conf.task_default_queue = "worker_queue"


@app.task(name="tasks.enqueue_job")
def enqueue_job(job_id):
    print(f"[Celery] Received job {job_id} for scheduling.")
    # Later the scheduler will pick it up from DB
    return f"Job {job_id} queued"

@app.task(name="tasks.execute_job")
def execute_job(job_id):
    """
    Simulates running the job, updates its status in DB.
    Later can be replaced with actual process execution logic.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"[Worker] Job {job_id} not found in DB.")
            return

        print(f"[Worker] Starting execution of job {job.name} (ID={job.id})")
        job.state = JobState.running
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Simulate execution time
        print(f"[Worker] Running command: {job.command}")
        time.sleep(20)  # placeholder for actual work

        # Mark as completed
        job.state = JobState.completed
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        print(f"[Worker] ✅ Job {job.name} completed successfully.")
        return f"Job {job.name} completed successfully."

    except SQLAlchemyError as e:
        print(f"[Worker] Database error while executing job {job_id}: {e}")
        db.rollback()
    except Exception as e:
        print(f"[Worker] General error while executing job {job_id}: {e}")
        db.rollback()
    finally:
        db.close()

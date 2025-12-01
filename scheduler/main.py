# scheduler/main.py
import os
from datetime import datetime, timezone, timedelta
from celery import Celery
from sqlalchemy.orm import Session
from api.db import SessionLocal
from api.models.job import Job, JobState, CarbonData
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    "scheduler",
    broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//"),
    backend="rpc://",
)

app.conf.task_default_queue = "scheduler_queue"

# -------------- periodic setup --------------
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, schedule_jobs.s(), name="Schedule waiting jobs every 10s")

# -------------- helper logic --------------
def get_latest_intensity(db: Session, zone: str) -> float | None:
    record = (
        db.query(CarbonData)
        .filter(CarbonData.zone.ilike(f"%{zone}%"))
        .order_by(CarbonData.datetime.desc())
        .first()
    )
    if record:
        print(f"[Scheduler] Found CI={record.carbon_intensity} for zone={record.zone}")
    return record.carbon_intensity if record else None


# -------------- main task --------------
@app.task
def schedule_jobs():
    """Decide which waiting jobs to release to execution based on carbon data."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        waiting_jobs = db.query(Job).filter(Job.state == JobState.waiting).all()
        
        # Sort jobs by priority: High > Deadline > Medium > Low
        # We need to calculate 'deadline_soon' for sorting, or just use urgency.
        # Let's define a priority key.
        def job_priority(j):
            # 0 = Highest Priority
            if j.urgency == "high":
                return 0
            
            # Check deadline
            if j.soft_deadline:
                if j.soft_deadline.tzinfo is None:
                    d = j.soft_deadline.replace(tzinfo=timezone.utc)
                else:
                    d = j.soft_deadline
                if (d - now) < timedelta(hours=1):
                    return 1 # Deadline soon
            
            if j.urgency == "medium":
                return 2
            return 3 # Low
            
        waiting_jobs.sort(key=job_priority)
        
        print(f"[Scheduler] Checking {len(waiting_jobs)} waiting jobs (Sorted by Priority)...")

        for job in waiting_jobs:
            ci = get_latest_intensity(db, job.preferred_zone)
            if ci is None:
                print(f"[Scheduler] No carbon data for {job.preferred_zone}, skipping {job.name}")
                continue

            # --- Decision logic ---
            run = False
            deadline_soon = False
            if job.soft_deadline:
                # Convert soft_deadline to timezone-aware UTC
                if job.soft_deadline.tzinfo is None:
                    job_deadline = job.soft_deadline.replace(tzinfo=timezone.utc)
                else:
                    job_deadline = job.soft_deadline
                deadline_soon = (job_deadline - now) < timedelta(hours=1)

            if job.urgency == "high":
                run = True
            elif job.urgency == "medium" and ci < 400:
                run = True
            elif job.urgency == "low" and ci < 300:
                run = True
            elif deadline_soon:
                run = True

            if run:
                print(f"[Scheduler] Scheduling job {job.name} (CI={ci})")
                job.state = JobState.running
                job.started_at = now
                job.carbon_intensity_at_run = ci
                db.commit()

                # send to execution queue (worker.tasks.execute_job)
                from celery import Celery
                exec_app = Celery("executor", broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//"))
                exec_app.send_task("tasks.execute_job", args=[job.id], queue="worker_queue")
            else:
                print(f"[Scheduler] Delaying job {job.name}, CI={ci}")

    except Exception as e:
        print("[Scheduler] Error:", e)
    finally:
        db.close()

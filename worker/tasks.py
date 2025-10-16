# worker/tasks.py
from celery import Celery

app = Celery(
    "carbon_scheduler",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://"
)

@app.task(name="tasks.enqueue_job")
def enqueue_job(job_id):
    print(f"[Celery] Received job {job_id} for scheduling.")
    # Later the scheduler will pick it up from DB
    return f"Job {job_id} queued"

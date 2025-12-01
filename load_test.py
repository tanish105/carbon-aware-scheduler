import requests
import random
from datetime import datetime, timedelta, timezone

API_URL = "http://localhost:8000/jobs/"
NUM_JOBS = 150  # Between 100 and 200

def generate_job():
    urgencies = ["high", "medium", "low"]
    urgency = random.choice(urgencies)
    
    # Random deadline: between 30 mins (urgent) and 5 hours from now
    minutes_offset = random.randint(30, 300)
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=minutes_offset)).isoformat()

    return {
        "name": f"job-{random.randint(1000, 9999)}",
        "command": "echo 'Hello World'",
        "resources": { "cpus": 4, "gpus": 0, "memory_gb": 16 },
        "expected_runtime_min": random.randint(5, 60),
        "urgency": urgency,
        "soft_deadline": deadline,
        "preferred_zone": "us-west1",
        "data_center_provider": "gcp"
    }

def submit_jobs():
    print(f"Submitting {NUM_JOBS} jobs...")
    for i in range(NUM_JOBS):
        job_data = generate_job()
        try:
            response = requests.post(API_URL, json=job_data)
            if response.status_code == 200:
                print(f"[{i+1}/{NUM_JOBS}] Submitted {job_data['name']} ({job_data['urgency']})")
            else:
                print(f"[{i+1}/{NUM_JOBS}] Failed: {response.text}")
        except Exception as e:
            print(f"[{i+1}/{NUM_JOBS}] Error: {e}")

if __name__ == "__main__":
    submit_jobs()

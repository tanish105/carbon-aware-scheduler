import time
import requests
import sys
from datetime import datetime, timedelta, timezone
from api.db import SessionLocal
from api.models.job import CarbonData, Job, JobState

API_URL = "http://localhost:8000/jobs/"
ZONE = "us-west1"

def print_header(msg):
    print(f"\n{'='*60}")
    print(f" {msg}")
    print(f"{'='*60}")

def inject_carbon_intensity(intensity):
    db = SessionLocal()
    try:
        # Create a new record with current time
        record = CarbonData(
            zone=ZONE,
            datetime=datetime.now(timezone.utc),
            carbon_intensity=intensity
        )
        db.add(record)
        db.commit()
        print(f"⚡ [INJECTED] Carbon Intensity for {ZONE}: {intensity} gCO2/kWh")
    except Exception as e:
        print(f"❌ Error injecting carbon data: {e}")
    finally:
        db.close()

def submit_job(name, urgency, deadline_hours=None):
    deadline = None
    if deadline_hours:
        deadline = (datetime.now(timezone.utc) + timedelta(hours=deadline_hours)).isoformat()
    
    payload = {
        "name": name,
        "command": f"echo 'Running {name}'",
        "resources": {"cpus": 0.1, "memory_gb": 0.128},
        "expected_runtime_min": 10,
        "urgency": urgency,
        "soft_deadline": deadline,
        "preferred_zone": ZONE
    }
    
    try:
        res = requests.post(API_URL, json=payload)
        if res.status_code == 200:
            job = res.json()
            print(f"📝 [SUBMITTED] Job '{name}' (ID: {job['id']}, Urgency: {urgency}, Deadline: {deadline_hours}h)")
        else:
            print(f"❌ Failed to submit job: {res.text}")
    except Exception as e:
        print(f"❌ Error submitting job: {e}")

def show_job_status():
    try:
        res = requests.get(API_URL)
        if res.status_code == 200:
            jobs = res.json()
            # Sort by ID to keep order stable
            jobs.sort(key=lambda x: x['id'])
            
            print(f"\n--- Job Status (Total: {len(jobs)}) ---")
            print(f"{'ID':<5} {'Name':<15} {'Urgency':<10} {'State':<12} {'Started At'}")
            print("-" * 60)
            for j in jobs:
                started = j['started_at'] if j['started_at'] else "-"
                print(f"{j['id']:<5} {j['name']:<15} {j['urgency']:<10} {j['state']:<12} {started}")
            print("-" * 60)
    except Exception as e:
        print(f"❌ Error fetching status: {e}")

def wait_and_watch(seconds):
    for i in range(seconds):
        sys.stdout.write(f"\r⏳ Waiting... {seconds-i}s ")
        sys.stdout.flush()
        time.sleep(1)
    print("\r" + " " * 20 + "\r", end="")

def get_latest_carbon_intensity():
    db = SessionLocal()
    try:
        # Get the most recent carbon data entry
        record = (
            db.query(CarbonData)
            .filter(CarbonData.zone == ZONE)
            .order_by(CarbonData.datetime.desc())
            .first()
        )
        return record.carbon_intensity if record else None
    except Exception:
        return None
    finally:
        db.close()

def run_demo():
    print_header("DEMO: Real-World Carbon-Aware Scheduling")
    print("NOTE: This demo relies on the REAL background fetcher.")
    print("      Ensure 'start_system.py' is running and you have a valid API key.")
    
    # 1. Submit 10 Jobs Simultaneously
    print("\n🚀 Submitting 10 mixed jobs simultaneously...")
    
    jobs_to_submit = [
        ("Job-1-High", "high", None),
        ("Job-2-High", "high", None),
        ("Job-3-Med", "medium", None),
        ("Job-4-Med", "medium", None),
        ("Job-5-Med", "medium", None),
        ("Job-6-Low", "low", None),
        ("Job-7-Low", "low", None),
        ("Job-8-Low", "low", None),
        ("Job-9-Deadline", "low", 0.5),  # Deadline in 30 mins
        ("Job-10-Deadline", "low", 0.8), # Deadline in 48 mins
    ]

    for name, urgency, deadline in jobs_to_submit:
        submit_job(name, urgency, deadline)
    
    print("\n✅ Jobs submitted. Monitoring system state...")
    print("Press Ctrl+C to exit monitoring.\n")

    try:
        while True:
            # Fetch latest CI
            ci = get_latest_carbon_intensity()
            ci_display = f"{ci} gCO2/kWh" if ci is not None else "WAITING FOR DATA..."
            
            print(f"\n[Current Grid State] Zone: {ZONE} | Intensity: {ci_display}")
            if ci is None:
                print("⚠️  WARNING: No carbon data found! Scheduler will skip jobs until data arrives.")
                print("   Check your .env file for ELECTRICITYMAP_TOKEN and ensure fetcher is running.")
            
            show_job_status()
            
            # Refresh every 5 seconds
            wait_and_watch(5)
            
    except KeyboardInterrupt:
        print("\nDemo stopped.")

if __name__ == "__main__":
    run_demo()

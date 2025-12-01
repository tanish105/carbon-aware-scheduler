import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- Configuration ---
API_URL = "http://127.0.0.1:8000"

# --- Shared Functions ---
def get_carbon_intensity():
    """Fetches the latest carbon intensity for us-west1."""
    try:
        response = requests.get(f"{API_URL}/carbon/latest/us-west1")
        if response.status_code == 200:
            data = response.json()
            return data.get("carbon_intensity")
    except requests.exceptions.ConnectionError:
        return None
    return None

def get_jobs():
    """Fetches all jobs from the API."""
    try:
        response = requests.get(f"{API_URL}/jobs/")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        return []
    return []

def submit_job(name, urgency, cpu, memory, deadline_hours):
    """Submits a new job to the API."""
    payload = {
        "name": name,
        "command": f"echo 'Running {name}'",
        "resources": {"cpus": cpu, "memory_gb": memory},
        "expected_runtime_min": 10,
        "urgency": urgency,
        "preferred_zone": "us-west1"
    }
    
    if deadline_hours > 0:
        # Calculate deadline timestamp
        future_time = datetime.utcnow().timestamp() + (deadline_hours * 3600)
        deadline_dt = datetime.fromtimestamp(future_time)
        payload["soft_deadline"] = deadline_dt.isoformat()

    try:
        response = requests.post(f"{API_URL}/jobs/", json=payload)
        return response.status_code == 200
    except:
        return False

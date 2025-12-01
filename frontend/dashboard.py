import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import os

# --- Configuration ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(
    page_title="Carbon-Aware Scheduler",
    page_icon="🌱",
    layout="wide",
)

# --- Styling ---
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    .status-running { color: #00cc00; font-weight: bold; }
    .status-waiting { color: #ff9900; font-weight: bold; }
    .status-completed { color: #0066cc; font-weight: bold; }
    .status-failed { color: #cc0000; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_carbon_intensity():
    try:
        # We'll use the 'us-west1' zone as default for the demo
        response = requests.get(f"{API_URL}/carbon/latest/us-west1")
        if response.status_code == 200:
            data = response.json()
            return data.get("carbon_intensity")
    except requests.exceptions.ConnectionError:
        return None
    return None

def get_jobs():
    try:
        response = requests.get(f"{API_URL}/jobs/")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        return []
    return []

def submit_job(name, urgency, cpu, memory, deadline_hours):
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
        # Note: In a real app, handle timezones carefully. 
        # Here we just send a future timestamp.
        # For simplicity in this demo, we might need to adjust how we send it 
        # depending on how the API expects it (ISO format).
        # The API expects ISO 8601 string.
        future_time = datetime.utcnow().timestamp() + (deadline_hours * 3600)
        deadline_dt = datetime.fromtimestamp(future_time)
        payload["soft_deadline"] = deadline_dt.isoformat()

    try:
        response = requests.post(f"{API_URL}/jobs/", json=payload)
        return response.status_code == 200
    except:
        return False

# --- Main Layout ---

st.title("🌱 Carbon-Aware Job Scheduler")

# Sidebar
with st.sidebar:
    st.header("Job Submission")
    with st.form("submit_job_form"):
        job_name = st.text_input("Job Name", value=f"Job-{int(time.time())}")
        urgency = st.selectbox("Urgency", ["low", "medium", "high"])
        col1, col2 = st.columns(2)
        with col1:
            cpu = st.number_input("CPUs", min_value=0.1, value=1.0, step=0.1)
        with col2:
            memory = st.number_input("Memory (GB)", min_value=0.1, value=1.0, step=0.1)
        
        deadline_hours = st.number_input("Deadline (Hours from now, 0 = None)", min_value=0.0, value=0.0, step=0.5)
        
        submitted = st.form_submit_button("🚀 Submit Job")
        
        if submitted:
            if submit_job(job_name, urgency, cpu, memory, deadline_hours):
                st.success(f"Job '{job_name}' submitted!")
                time.sleep(1) # Give API a moment
                st.rerun()
            else:
                st.error("Failed to submit job. Is the API running?")

# Top Metrics
ci = get_carbon_intensity()

col1, col2, col3 = st.columns(3)
with col1:
    if ci is not None:
        delta_color = "normal"
        if ci < 300:
            status = "🌿 Clean Grid"
            delta_color = "normal" # Streamlit handles green for positive delta, but we want custom logic
        elif ci < 400:
            status = "⚠️ Moderate Grid"
            delta_color = "off"
        else:
            status = "🏭 Dirty Grid"
            delta_color = "inverse"
        
        st.metric("Carbon Intensity (us-west1)", f"{ci} gCO₂/kWh", status)
    else:
        st.metric("Carbon Intensity", "Offline", "Check API")

with col2:
    st.info("High Urgency: Runs Immediately")
    
with col3:
    st.warning("Low Urgency: Waits for CI < 300")

# Job Table
st.subheader("Job Queue")

jobs = get_jobs()

if jobs:
    df = pd.DataFrame(jobs)
    
    # Select and Rename Columns
    if not df.empty:
        # Handle missing columns gracefully
        cols_to_keep = ["id", "name", "urgency", "state", "created_at", "started_at", "completed_at", "carbon_intensity_at_run"]
        existing_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[existing_cols]
        
        # Format Timestamps
        for col in ["created_at", "started_at", "completed_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%H:%M:%S')

        # Styling the dataframe
        st.dataframe(
            df.sort_values(by="id", ascending=False),
            use_container_width=True,
            column_config={
                "state": st.column_config.TextColumn(
                    "State",
                    help="Current status of the job",
                    validate="^.*$",
                ),
                "urgency": st.column_config.TextColumn(
                    "Urgency",
                ),
            },
            hide_index=True,
        )
else:
    st.info("No jobs found. Submit one from the sidebar!")

# Auto-refresh
time.sleep(2)
st.rerun()

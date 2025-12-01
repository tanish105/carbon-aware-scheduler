import streamlit as st
import pandas as pd
import time
from utils import get_jobs

st.set_page_config(page_title="Job Monitor", page_icon="👀", layout="wide")

st.markdown("# 👀 Job Monitor")
st.markdown("Real-time view of the scheduler's queue.")

# --- Filters ---
col1, col2 = st.columns(2)
with col1:
    filter_state = st.multiselect("Filter by State", ["waiting", "running", "completed", "cancelled"])
with col2:
    filter_urgency = st.multiselect("Filter by Urgency", ["low", "medium", "high"])

# --- Data Fetching ---
jobs = get_jobs()

if jobs:
    df = pd.DataFrame(jobs)
    
    # Apply Filters
    if filter_state:
        df = df[df["state"].isin(filter_state)]
    if filter_urgency:
        df = df[df["urgency"].isin(filter_urgency)]
        
    # Select and Rename Columns
    if not df.empty:
        cols_to_keep = ["id", "name", "urgency", "state", "created_at", "started_at", "completed_at", "carbon_intensity_at_run"]
        existing_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[existing_cols]
        
        # Format Timestamps
        for col in ["created_at", "started_at", "completed_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%H:%M:%S')

        # Styling
        st.dataframe(
            df.sort_values(by="id", ascending=False),
            use_container_width=True,
            column_config={
                "state": st.column_config.TextColumn(
                    "State",
                    help="Current status of the job",
                    validate="^.*$",
                ),
                "carbon_intensity_at_run": st.column_config.NumberColumn(
                    "CI at Run",
                    format="%.0f gCO2/kWh"
                )
            },
            hide_index=True,
        )
    else:
        st.info("No jobs match your filters.")
else:
    st.warning("No jobs found in the system.")

# Auto-refresh
time.sleep(5)
st.rerun()

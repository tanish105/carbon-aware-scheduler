import streamlit as st
import time
from utils import get_carbon_intensity, get_jobs

# --- Page Config ---
st.set_page_config(
    page_title="Carbon-Aware Scheduler",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Styling ---
# Using Streamlit's native metrics and containers for better dark mode support.
# Only adding minimal custom CSS for specific highlights.
st.markdown("""
<style>
    /* Custom highlight for the carbon intensity value */
    .ci-value {
        font-size: 3rem;
        font-weight: bold;
    }
    .status-clean { color: #4CAF50; }
    .status-moderate { color: #FFC107; }
    .status-dirty { color: #F44336; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🌱 Carbon-Aware Job Scheduler")
st.markdown("### Intelligent workload management for a greener grid.")

# --- Main Dashboard ---
# Auto-refresh logic
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Fetch Data
ci = get_carbon_intensity()
jobs = get_jobs()

# --- Carbon Intensity Display ---
st.divider()
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Current Grid Status")
    if ci is not None:
        if ci < 300:
            status_color = "status-clean"
            status_text = "🌿 Clean Grid"
            msg = "Great time to run Low Urgency jobs!"
        elif ci < 400:
            status_color = "status-moderate"
            status_text = "⚠️ Moderate Grid"
            msg = "Medium Urgency jobs are running."
        else:
            status_color = "status-dirty"
            status_text = "🏭 Dirty Grid"
            msg = "Only High Urgency jobs will run."
        
        st.markdown(f'<div class="ci-value {status_color}">{ci} gCO₂/kWh</div>', unsafe_allow_html=True)
        st.markdown(f"**{status_text}**")
        st.info(msg)
    else:
        st.error("🔌 API Offline")
        st.caption("Ensure `start_system.py` is running.")

with col2:
    st.subheader("System Overview")
    
    # Calculate Stats
    total_jobs = len(jobs)
    running = len([j for j in jobs if j['state'] == 'running'])
    waiting = len([j for j in jobs if j['state'] == 'waiting'])
    completed = len([j for j in jobs if j['state'] == 'completed'])
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jobs", total_jobs)
    m2.metric("Running", running)
    m3.metric("Waiting", waiting)
    m4.metric("Completed", completed)
    
    st.markdown("---")
    st.markdown("""
    **How it works:**
    1.  **Submit** a job with an urgency level.
    2.  **Scheduler** checks the Carbon Intensity (CI).
    3.  **High** jobs run immediately.
    4.  **Medium** jobs wait for CI < 400.
    5.  **Low** jobs wait for CI < 300 (unless deadline approaches).
    """)

# --- Sidebar ---
st.sidebar.success("Select a page above to Submit or Monitor jobs.")
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {time.strftime('%H:%M:%S')}")

# Auto-refresh every 10 seconds
time.sleep(10)
st.rerun()

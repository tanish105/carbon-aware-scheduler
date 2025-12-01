import streamlit as st
import time
from utils import submit_job

st.set_page_config(page_title="Submit Job", page_icon="🚀")

st.markdown("# 🚀 Submit a New Job")
st.markdown("Define your workload requirements below.")

with st.form("submit_job_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        job_name = st.text_input("Job Name", value=f"Job-{int(time.time())}", help="Unique identifier for this job.")
        urgency = st.selectbox(
            "Urgency Level", 
            ["low", "medium", "high"],
            help="High: Runs immediately. Medium: Waits for <400 CI. Low: Waits for <300 CI."
        )
    
    with col2:
        cpu = st.number_input("CPUs Required", min_value=0.1, value=1.0, step=0.1)
        memory = st.number_input("Memory Required (GB)", min_value=0.1, value=1.0, step=0.1)
    
    st.divider()
    
    deadline_hours = st.number_input(
        "Soft Deadline (Hours from now)", 
        min_value=0.0, 
        value=0.0, 
        step=0.5,
        help="If set, the scheduler will prioritize this job as the deadline approaches, ignoring carbon intensity if necessary."
    )
    
    submitted = st.form_submit_button("Submit Job", type="primary")
    
    if submitted:
        with st.spinner("Submitting to Scheduler..."):
            if submit_job(job_name, urgency, cpu, memory, deadline_hours):
                st.success(f"✅ Job **{job_name}** submitted successfully!")
                st.balloons()
                time.sleep(2)
            else:
                st.error("❌ Failed to submit job. Please check if the API is running.")

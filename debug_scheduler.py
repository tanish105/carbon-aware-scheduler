import sys
import os

# Ensure we can import from root
sys.path.append(os.getcwd())

try:
    from scheduler.main import schedule_jobs
    print("✅ Successfully imported scheduler.main.schedule_jobs")
except Exception as e:
    print(f"❌ Failed to import scheduler: {e}")
    sys.exit(1)

print("Running schedule_jobs() manually...")
try:
    schedule_jobs()
    print("✅ schedule_jobs() executed successfully.")
except Exception as e:
    print(f"❌ Error running schedule_jobs: {e}")
    import traceback
    traceback.print_exc()

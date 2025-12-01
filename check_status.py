from api.db import SessionLocal
from api.models.job import Job, JobState
from sqlalchemy import func

def check_status():
    db = SessionLocal()
    try:
        # Count jobs by state
        results = db.query(Job.state, func.count(Job.state)).group_by(Job.state).all()
        
        print("\n--- Job Status Report ---")
        if not results:
            print("No jobs found in the database.")
        else:
            total = 0
            for state, count in results:
                print(f"{state.value}: {count}")
                total += count
            print(f"Total Jobs: {total}")
        print("-------------------------\n")
        
    except Exception as e:
        print(f"Error checking status: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_status()

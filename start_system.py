import subprocess
import sys
import time

def start_process(command, name):
    print(f"Starting {name}...")
    return subprocess.Popen(
        command,
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

def main():
    processes = []
    try:
        # API
        processes.append(start_process("python -m uvicorn api.main:app --reload --port 8000", "API"))
        
        # Worker
        processes.append(start_process("python -m celery -A worker.tasks worker -Q worker_queue --loglevel=info --pool=solo", "Worker"))
        
        # Carbon Fetcher
        processes.append(start_process("python -m celery -A carbon_data.fetcher beat --loglevel=info", "Carbon Fetcher (Beat)"))
        processes.append(start_process("python -m celery -A carbon_data.fetcher worker -Q carbon_data_queue --loglevel=info --pool=solo", "Carbon Fetcher (Worker)"))
        
        # Scheduler
        processes.append(start_process("python -m celery -A scheduler.main beat --loglevel=info", "Scheduler (Beat)"))
        processes.append(start_process("python -m celery -A scheduler.main worker -Q scheduler_queue --loglevel=info --pool=solo", "Scheduler (Worker)"))

        print("\nAll components started. Press Ctrl+C to stop all.\n")
        
        # Keep main process alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all processes...")
        for p in processes:
            p.terminate()
        print("Done.")

if __name__ == "__main__":
    main()

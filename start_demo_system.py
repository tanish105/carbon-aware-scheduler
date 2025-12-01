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
        
        # Scheduler (Beat + Worker)
        processes.append(start_process("python -m celery -A scheduler.main beat --loglevel=info", "Scheduler (Beat)"))
        processes.append(start_process("python -m celery -A scheduler.main worker -Q scheduler_queue --loglevel=info --pool=solo", "Scheduler (Worker)"))

        # NOTE: We do NOT start the Carbon Fetcher here.
        # This allows the demo script to inject its own carbon data without interference.

        print("\n✅ Demo System started (No Fetcher). Press Ctrl+C to stop all.\n")
        
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

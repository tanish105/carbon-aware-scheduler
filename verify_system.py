import socket
import requests
import os
import sys
from celery import Celery
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def check_port(host, port, name):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"✅ {name} is reachable on {host}:{port}")
            return True
    except (socket.timeout, ConnectionRefusedError):
        print(f"❌ {name} is NOT reachable on {host}:{port}")
        return False

def check_api():
    url = "http://127.0.0.1:8000/docs"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ API is running (Docs available at {url})")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API is NOT running")
    return False

def check_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_rabbitmq():
    # Basic port check for AMQP
    if check_port("localhost", 5672, "RabbitMQ (AMQP)"):
        # Try Celery connection
        try:
            app = Celery("test", broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//"))
            with app.connection_or_acquire() as conn:
                conn.ensure_connection(max_retries=1)
            print("✅ Celery can connect to RabbitMQ")
            
            # Inspect workers
            i = app.control.inspect()
            active = i.active()
            if active:
                print(f"✅ Found {len(active)} active Celery worker(s)")
                for worker, tasks in active.items():
                    print(f"   - {worker}: {len(tasks)} tasks running")
            else:
                print("⚠️  No active Celery workers found (Is 'start_system.py' running?)")
            return True
        except Exception as e:
            print(f"❌ Celery connection failed: {e}")
    return False

if __name__ == "__main__":
    print("--- System Verification ---")
    components = [
        check_port("localhost", 5432, "PostgreSQL"),
        check_rabbitmq(),
        check_db(),
        check_api(),
    ]
    
    if all(components):
        print("\n✨ All systems go!")
    else:
        print("\n⚠️  Some components are down. Check the logs above.")

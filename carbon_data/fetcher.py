# carbon_data/fetcher.py
import os
import requests
from celery import Celery
from datetime import datetime, timezone
from api.db import SessionLocal
from api.models.job import CarbonData
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -----------------------------
# Celery Configuration
# -----------------------------
app = Celery(
    "carbon_data_fetcher",
    broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//"),
    backend="rpc://"
)

# -----------------------------
# Environment Variables
# -----------------------------
ELECTRICITYMAP_TOKEN = os.getenv("ELECTRICITYMAP_TOKEN", "YOUR_API_KEY")
DATA_CENTER_REGION = os.getenv("DATA_CENTER_REGION", "us-west1")
DATA_CENTER_PROVIDER = os.getenv("DATA_CENTER_PROVIDER", "gcp")

# -----------------------------
# Celery Beat Schedule (every 5 min)
# -----------------------------
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every 5 minutes (300 seconds)
    sender.add_periodic_task(300.0, fetch_carbon_data.s(), name="Fetch carbon data every 5m")

# -----------------------------
# Main Task
# -----------------------------
@app.task
def fetch_carbon_data():
    """
    Periodically fetch carbon intensity data from ElectricityMap API
    and store it in PostgreSQL.
    """
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d+%H:%M")

        # Updated endpoint for data center regions
        url = (
            f"https://api.electricitymaps.com/v3/carbon-intensity/past"
            f"?dataCenterRegion={DATA_CENTER_REGION}"
            f"&dataCenterProvider={DATA_CENTER_PROVIDER}"
            f"&datetime={now}"
        )

        print(f"[Fetcher] Fetching carbon intensity for {DATA_CENTER_REGION} ({DATA_CENTER_PROVIDER}) at {now}...")

        response = requests.get(
            url,
            headers={"auth-token": ELECTRICITYMAP_TOKEN},
            timeout=10  # <-- avoids hanging requests
        )

        if response.status_code != 200:
            print(f"[Fetcher] Error {response.status_code}: {response.text}")
            return

        data = response.json()
        carbon_intensity = data.get("carbonIntensity")
        timestamp = data.get("datetime", now)
        zone = data.get("zone", DATA_CENTER_REGION)

        if not carbon_intensity:
            print("[Fetcher] Warning: No carbon intensity data in response.")
            return

        # Store record in DB
        db = SessionLocal()
        record = CarbonData(
            zone=zone,
            datetime=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
            carbon_intensity=carbon_intensity,
        )
        db.add(record)
        db.commit()
        db.close()

        print(f"[Fetcher] ✅ Stored {carbon_intensity} gCO₂/kWh for {zone} ({DATA_CENTER_PROVIDER})")

    except SQLAlchemyError as e:
        print("[Fetcher] ❌ Database error:", e)
    except requests.exceptions.RequestException as e:
        print("[Fetcher] ❌ API request error:", e)
    except Exception as e:
        print("[Fetcher] ❌ Unexpected error:", e)

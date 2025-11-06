# carbon_data/fetcher.py
import os
import requests
from celery import Celery
from datetime import datetime, timezone
from api.db import SessionLocal
from api.models.job import CarbonData
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    "carbon_data_fetcher",
    broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//"),
    backend="rpc://"
)

ELECTRICITYMAP_TOKEN = os.getenv("ELECTRICITYMAP_TOKEN", "YOUR_API_KEY")
ZONE = os.getenv("CARBON_ZONE", "AT")  # default to Austria, change as needed

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # run every 5 minutes (300 seconds)
    sender.add_periodic_task(300.0, fetch_carbon_data.s(), name="Fetch carbon data every 5m")

@app.task
def fetch_carbon_data():
    """
    Fetch latest carbon intensity data from ElectricityMap and store it in DB.
    """
    try:
        # Build API URL
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d+%H:%M")
        url = f"https://api.electricitymaps.com/v3/carbon-intensity/past?zone={ZONE}&datetime={now}&disableEstimations=true"

        response = requests.get(
            url,
            headers={"auth-token": ELECTRICITYMAP_TOKEN}
        )

        if response.status_code != 200:
            print(f"[Fetcher] Error: {response.status_code} - {response.text}")
            return

        data = response.json()
        carbon_intensity = data.get("carbonIntensity", 0.0)
        timestamp = data.get("datetime", now)

        db = SessionLocal()
        record = CarbonData(
            zone=ZONE,
            datetime=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
            carbon_intensity=carbon_intensity
        )
        db.add(record)
        db.commit()
        db.close()

        print(f"[Fetcher] Stored carbon intensity {carbon_intensity} gCO2/kWh for zone {ZONE}")

    except SQLAlchemyError as e:
        print("[Fetcher] Database error:", e)
    except Exception as e:
        print("[Fetcher] General error:", e)

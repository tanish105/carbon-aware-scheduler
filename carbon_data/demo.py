# demo.py
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from api.db import SessionLocal, engine
from api.models.job import Base, CarbonData

# Load environment variables
load_dotenv()

ELECTRICITYMAP_TOKEN = os.getenv("ELECTRICITYMAP_TOKEN", "YOUR_API_KEY")
DATA_CENTER_REGION = os.getenv("DATA_CENTER_REGION", "us-west1")
DATA_CENTER_PROVIDER = os.getenv("DATA_CENTER_PROVIDER", "gcp")

def fetch_and_store_carbon_data():
    """Fetch carbon intensity data from ElectricityMap and store it in PostgreSQL."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d+%H:%M")

    url = (
        f"https://api.electricitymaps.com/v3/carbon-intensity/past"
        f"?dataCenterRegion={DATA_CENTER_REGION}"
        f"&dataCenterProvider={DATA_CENTER_PROVIDER}"
        f"&datetime={now}"
    )

    print(f"[INFO] Fetching carbon intensity for {DATA_CENTER_REGION} ({DATA_CENTER_PROVIDER}) at {now}...")
    response = requests.get(
        url,
        headers={"auth-token": ELECTRICITYMAP_TOKEN}
    )

    if response.status_code != 200:
        print(f"[ERROR] API request failed: {response.status_code} - {response.text}")
        return

    data = response.json()
    carbon_intensity = data.get("carbonIntensity")
    timestamp = data.get("datetime", now)

    if not carbon_intensity:
        print("[WARN] No carbon intensity data found in response.")
        return

    db = SessionLocal()
    record = CarbonData(
        zone=data.get("zone", DATA_CENTER_REGION),
        datetime=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
        carbon_intensity=carbon_intensity,
    )
    db.add(record)
    db.commit()
    db.close()

    print(f"[SUCCESS] Stored carbon intensity {carbon_intensity} gCO₂/kWh for {DATA_CENTER_REGION} ({DATA_CENTER_PROVIDER})")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    fetch_and_store_carbon_data()

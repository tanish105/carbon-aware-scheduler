from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db import SessionLocal
from api.models.job import CarbonData

router = APIRouter(prefix="/carbon", tags=["Carbon Data"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/latest")
def get_latest_carbon_data(db: Session = Depends(get_db)):
    record = db.query(CarbonData).order_by(CarbonData.datetime.desc()).first()
    if not record:
        raise HTTPException(status_code=404, detail="No carbon data found")
    return {
        "zone": record.zone,
        "datetime": record.datetime,
        "carbon_intensity": record.carbon_intensity,
    }

#latest with zone query param
@router.get("/latest/{zone}")
def get_latest_carbon_data_by_zone(zone: str, db: Session = Depends(get_db)):
    record = (
        db.query(CarbonData)
        .filter(CarbonData.zone == zone)
        .order_by(CarbonData.datetime.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail=f"No carbon data found for zone {zone}")
    return {
        "zone": record.zone,
        "datetime": record.datetime,
        "carbon_intensity": record.carbon_intensity,
    }

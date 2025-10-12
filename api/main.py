from fastapi import FastAPI
from api.db import SessionLocal
from api.models import job

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Carbon Aware Scheduler API running"}

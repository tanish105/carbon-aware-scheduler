# api/main.py
from fastapi import FastAPI
from api.routes import job_routes

app = FastAPI(title="Carbon Aware Scheduler API")
app.include_router(job_routes.router)

@app.get("/")
def read_root():
    return {"message": "Carbon Aware Scheduler API running"}

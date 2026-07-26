# backend/app/main.py
from fastapi import FastAPI
from app.core.database import Base, engine
from app.api.v1.endpoints import ingestion

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenTax Predictive Cashflow API")

app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
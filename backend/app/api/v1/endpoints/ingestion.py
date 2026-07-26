# backend/app/api/v1/endpoints/ingestion.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tally_payload import TallyPayload
from app.services.tax_calculator import upsert_daily_tax_event

router = APIRouter()


@router.post("/daily-delta", status_code=200)
def ingest_daily_delta(payload: TallyPayload, db: Session = Depends(get_db)):
    event = upsert_daily_tax_event(db, payload.model_dump())
    return {"status": "success", "company_id": event.company_id, "date": str(event.date)}
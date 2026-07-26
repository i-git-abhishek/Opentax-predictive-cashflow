from typing import Literal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.tax_event import AlertHistory
from app.services.tax_calculator import calculate_current_month_liability
from app.services.whatsapp_service import send_whatsapp_message, get_alert_message_body
from app.jobs.scheduler import scheduler
from app.core.config import settings

router = APIRouter(prefix="/alerts", tags=["Alerts System"])

class TriggerRequest(BaseModel):
    company_id: str = Field(default="C-1002", description="Target Company Identifier")
    alert_type: Literal["FORECAST", "FINAL_SUMMARY"] = Field(default="FORECAST", description="Alert Type to trigger")
    to_number: str | None = Field(default=None, description="Optional override phone number (e.g. whatsapp:+919999999999)")

class JobStatusResponse(BaseModel):
    job_id: str
    trigger: str
    next_run_time: str | None

@router.post("/test-trigger", status_code=status.HTTP_200_OK)
def trigger_alert_manually(payload: TriggerRequest, db: Session = Depends(get_db)):
    """
    Manually dispatch a Forecast or Final Summary alert on demand.
    Queries the live database, runs calculation, formats templated body, dispatches, and logs.
    """
    company_id = payload.company_id
    alert_type = payload.alert_type
    recipient = payload.to_number or settings.DEFAULT_TO_WHATSAPP_NUMBER

    try:
        # 1. Fetch liability calculation from database
        liability = calculate_current_month_liability(db, company_id)

        # 2. Format the WhatsApp message body
        body = get_alert_message_body(alert_type, date.today(), liability)

        # 3. Create Audit Ledger Entry (PENDING status)
        audit_log = AlertHistory(
            company_id=company_id,
            alert_type=alert_type,
            recipient=recipient,
            message_body=body,
            status="PENDING",
            retry_count=0
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        # 4. Fire WhatsApp message with retry policy
        result = send_whatsapp_message(recipient, body)

        # 5. Update Audit Ledger with delivery results
        audit_log.status = result["status"]
        audit_log.retry_count = result["retry_count"]
        audit_log.error_message = result["error_message"]
        db.commit()
        db.refresh(audit_log)

        return {
            "message": "Manual alert dispatch completed",
            "details": {
                "audit_id": audit_log.id,
                "company_id": company_id,
                "alert_type": alert_type,
                "recipient": recipient,
                "message_body": body,
                "status": audit_log.status,
                "retry_count": audit_log.retry_count,
                "error_message": audit_log.error_message
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while executing manual trigger: {str(e)}"
        )

@router.get("/scheduler-status", response_model=list[JobStatusResponse])
def get_scheduler_status():
    """
    Control Plane Diagnostic endpoint.
    Retrieves all registered jobs running in the APScheduler background thread.
    """
    jobs = scheduler.get_jobs()
    job_statuses = []
    for job in jobs:
        job_statuses.append(
            JobStatusResponse(
                job_id=job.id,
                trigger=str(job.trigger),
                next_run_time=str(job.next_run_time) if job.next_run_time else None
            )
        )
    return job_statuses

@router.get("/history")
def get_alert_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieve logs of outgoing alerts from the database-backed deliverability ledger.
    """
    logs = db.query(AlertHistory).order_by(AlertHistory.created_at.desc()).limit(limit).all()
    return logs

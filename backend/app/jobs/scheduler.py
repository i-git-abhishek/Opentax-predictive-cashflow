import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.tax_event import AlertHistory
from app.services.tax_calculator import calculate_current_month_liability
from app.services.whatsapp_service import send_whatsapp_message, get_alert_message_body

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

async def run_tax_alert_job(alert_type: str):
    """
    Core executor for tax alerts.
    Fetches monthly liability, formats text, fires WhatsApp message, and logs execution to Audit ledger.
    """
    logger.info(f"Triggering background job: {alert_type}")
    db = SessionLocal()
    try:
        company_id = settings.DEFAULT_COMPANY_ID
        recipient = settings.DEFAULT_TO_WHATSAPP_NUMBER
        
        # 1. Calculate liability
        liability = calculate_current_month_liability(db, company_id)
        
        # 2. Format message body
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
        
        # 4. Dispatch WhatsApp message
        result = send_whatsapp_message(recipient, body)
        
        # 5. Update Audit Ledger with delivery results
        audit_log.status = result["status"]
        audit_log.retry_count = result["retry_count"]
        audit_log.error_message = result["error_message"]
        db.commit()
        
        logger.info(f"Finished background job: {alert_type}. Status: {result['status']}")
    except Exception as e:
        logger.error(f"Uncaught exception in background job {alert_type}: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    """
    Registers the jobs and starts the scheduler.
    """
    # Check if a custom debug interval is set for local testing
    if settings.SCHEDULER_INTERVAL_MINUTES is not None:
        interval_min = settings.SCHEDULER_INTERVAL_MINUTES
        logger.info(f"DEBUG MODE: Registering background tasks to run every {interval_min} minute(s)")
        
        scheduler.add_job(
            run_tax_alert_job,
            IntervalTrigger(minutes=interval_min),
            args=["FORECAST"],
            id="debug_forecast_job",
            replace_existing=True
        )
        
        scheduler.add_job(
            run_tax_alert_job,
            IntervalTrigger(minutes=interval_min),
            args=["FINAL_SUMMARY"],
            id="debug_final_summary_job",
            replace_existing=True
        )
    else:
        # Standard Production Cron Triggers
        logger.info("PRODUCTION MODE: Registering standard monthly cron tasks")
        
        # Job A: Forecast on 25th at 9:00 AM
        scheduler.add_job(
            run_tax_alert_job,
            CronTrigger(day=25, hour=9, minute=0),
            args=["FORECAST"],
            id="monthly_forecast_job",
            replace_existing=True
        )
        
        # Job B: Final Bill on 1st at 9:00 AM
        scheduler.add_job(
            run_tax_alert_job,
            CronTrigger(day=1, hour=9, minute=0),
            args=["FINAL_SUMMARY"],
            id="monthly_final_summary_job",
            replace_existing=True
        )

    scheduler.start()
    logger.info("APScheduler started successfully.")

def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler shut down successfully.")

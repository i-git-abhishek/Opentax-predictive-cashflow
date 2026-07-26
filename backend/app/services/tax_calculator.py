from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from app.models.tax_event import DailyTaxEvent

def upsert_daily_tax_event(db: Session, payload: dict):
    company_id = payload.get("company_id")
    # Handle parsing date from string if necessary
    event_date = payload.get("date")
    if isinstance(event_date, str):
        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()

    daily_sales_tax = payload.get("daily_sales_tax", 0.0)
    daily_purchase_tax = payload.get("daily_purchase_tax", 0.0)

    tax_event = db.query(DailyTaxEvent).filter(
        DailyTaxEvent.company_id == company_id,
        DailyTaxEvent.date == event_date
    ).first()

    if tax_event:
        tax_event.daily_sales_tax = daily_sales_tax
        tax_event.daily_purchase_tax = daily_purchase_tax
    else:
        tax_event = DailyTaxEvent(
            company_id=company_id,
            date=event_date,
            daily_sales_tax=daily_sales_tax,
            daily_purchase_tax=daily_purchase_tax
        )
        db.add(tax_event)
    
    db.commit()
    db.refresh(tax_event)
    return tax_event

def calculate_current_month_liability(db: Session, company_id: str):
    today = date.today()
    current_year = today.year
    current_month = today.month

    result = db.query(
        func.sum(DailyTaxEvent.daily_sales_tax).label('total_sales_tax'),
        func.sum(DailyTaxEvent.daily_purchase_tax).label('total_purchase_tax')
    ).filter(
        DailyTaxEvent.company_id == company_id,
        extract('year', DailyTaxEvent.date) == current_year,
        extract('month', DailyTaxEvent.date) == current_month
    ).first()

    total_sales_tax = result.total_sales_tax or 0.0
    total_purchase_tax = result.total_purchase_tax or 0.0
    net_liability = total_sales_tax - total_purchase_tax

    return net_liability
    

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint, func
from app.core.database import Base

class DailyTaxEvent(Base):
    __tablename__ = "daily_tax_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    daily_sales_tax = Column(Float, nullable=False, default=0.0)
    daily_purchase_tax = Column(Float, nullable=False, default=0.0)

    # Prevent duplicate rows for the same company and day
    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uq_company_date"),
    )

class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, nullable=False, index=True)
    alert_type = Column(String, nullable=False) # e.g., "FORECAST" or "FINAL_SUMMARY"
    recipient = Column(String, nullable=False)
    message_body = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING") # "SENT", "FAILED", "PENDING"
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

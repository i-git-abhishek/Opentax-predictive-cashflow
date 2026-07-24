from sqlalchemy import Column, Integer, String, Date, Float, UniqueConstraint
from app.core.database import Base

class DailyTaxEvent(Base):
    __tablename__ = "daily_tax_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    daily_sales_tax = Column(Float, nullable=False, default=0.0)
    daily_purchase_tax = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint('company_id', 'date', name='uq_company_date'),
    )

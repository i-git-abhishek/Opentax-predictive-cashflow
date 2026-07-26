from pydantic import BaseModel, ConfigDict
from datetime import date


class TallyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    date: date
    daily_sales_tax: float
    daily_purchase_tax: float
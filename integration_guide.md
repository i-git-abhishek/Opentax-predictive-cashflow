# OpenTax Predictive Cashflow - Multi-Team Integration Guide

This guide outlines how **Team 1 (Tally & Edge Integration)** and **Team 2 (Database & Logic Layer)** can plug their systems directly into the backend infrastructure established by **Team 3 (Scheduler & Messaging)**.

---

## 📂 Backend Architecture Map

Here is the directory structure we built in the `backend/` folder. The highlighted files are the integration touchpoints for each team:

```
opentax-predictive-cashflow/
└── backend/
    ├── .env                         # System configuration file (Twilio, Database URL, testing schedules)
    ├── seed_data.py                 # Seeds mock daily tax events to database for local checks
    └── app/
        ├── main.py                  # FastAPI initialization & scheduler lifespan hooks
        ├── api/v1/endpoints/
        │   ├── ingest.py            # <-- [TEAM 1 INTEGRATION] Receives Tally pushes
        │   └── alerts.py            # <-- Administrative control (Manual trigger, Diagnostic routes)
        ├── core/
        │   ├── config.py            # Configures environment variables (Pydantic Settings)
        │   └── database.py          # <-- [TEAM 2 INTEGRATION] DB connections, Engine & SessionLocal
        ├── models/
        │   └── tax_event.py         # <-- [TEAM 2 INTEGRATION] Table schemas: DailyTaxEvent, AlertHistory
        └── services/
            ├── tax_calculator.py    # <-- [TEAM 2 INTEGRATION] Math aggregation & Upsert logic
            └── whatsapp_service.py  # Twilio client wrapper (Retry policies, Alert templates)
```

---

## 🤝 Team 1: Tally & Edge Integration (Edge Pushes)

Team 1 extracts financial logs from TallyPrime and transmits them to the cloud backend.

### 1. Ingestion Endpoint
Team 1 must configure their TDL script or `mock_tally_sender.py` script to perform an **HTTP POST** request to:
```http
POST http://localhost:8000/api/v1/ingest/daily-delta
Content-Type: application/json
```

### 2. Ingestion JSON Schema (API Contract)
The request payload must match this schema exactly:
```json
{
  "company_id": "C-1002",
  "date": "2026-07-25",
  "daily_sales_tax": 4500.00,
  "daily_purchase_tax": 1500.00
}
```

### 3. Example Team 1 Python Sender Code
Team 1 can use the following python code structure in their sender script to push data:
```python
import requests
from datetime import date

payload = {
    "company_id": "C-1002",
    "date": str(date.today()), # Must match YYYY-MM-DD
    "daily_sales_tax": 4500.00,
    "daily_purchase_tax": 1500.00
}

response = requests.post(
    "http://localhost:8000/api/v1/ingest/daily-delta",
    json=payload
)

if response.status_code == 200:
    print("Ingestion Successful:", response.json())
else:
    print(f"Error {response.status_code}:", response.text)
```

---

## 🤝 Team 2: Database & Logic Layer (Engine & Math)

Team 2 owns the SQLite database configurations, SQLAlchemy model definitions, and tax liability calculation formulas.

We have structured the backend so Team 2 can drop in their implementations with **zero disruption** to our endpoints or scheduled tasks.

### 1. Database Connection (`app/core/database.py`)
If Team 2 changes the database connection string or transitions from SQLite to PostgreSQL/MySQL, they only need to modify:
1. The `DATABASE_URL` parameter in the `.env` file (e.g. `DATABASE_URL=postgresql://user:pass@localhost:5432/dbname`).
2. If they need database-specific driver arguments, they can modify them in `database.py`.

### 2. ORM Tables & Models (`app/models/tax_event.py`)
Team 2 owns the class definitions. We created the following baseline structures:
* **`DailyTaxEvent`**: Stores daily sums. Must maintain the unique constraint:
  ```python
  __table_args__ = (UniqueConstraint("company_id", "date", name="uq_company_date"),)
  ```
* **`AlertHistory`**: (Team 3 Auditing Ledger). **Team 2 must not modify or delete this table**, as it tracks the message statuses and retry attempts for notifications.

### 3. Calculations Logic (`app/services/tax_calculator.py`)
Team 2 must supply the logic inside this file. They must implement and export two functions matching these exact signatures:

#### A. The Ingestion Upsert Function:
Called automatically when Team 1 pushes daily aggregates.
```python
def upsert_daily_tax_event(db: Session, payload: dict) -> DailyTaxEvent:
    # Logic:
    # 1. Look for row matching company_id and date
    # 2. If exists, update daily_sales_tax and daily_purchase_tax columns
    # 3. If not, insert a new row
```

#### B. The Liability Calculation Function:
Called automatically by Team 3's background scheduler and manual endpoints.
```python
def calculate_current_month_liability(db: Session, company_id: str) -> float:
    # Formula: Sum(Sales Tax) - Sum(Purchase Tax)
    # Filtered by: current month and current year
```
*Note: Make sure to extract both the `month` and `year` dynamically when querying the date column, ensuring historical months do not leak into the current month's totals.*

---

## 🚀 Running & Verifying the Integrated Pipeline

When all parts are connected, follow these steps to execute the system:

1. **Start the application server**:
   ```bash
   uvicorn app.main:app --reload
   ```
2. **Team 1 pushes invoice updates** (simulates voucher save in Tally):
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/ingest/daily-delta \
     -H "Content-Type: application/json" \
     -d '{"company_id": "C-1002", "date": "2026-07-25", "daily_sales_tax": 20000.0, "daily_purchase_tax": 8000.0}'
   ```
3. **Inspect calculations & send alerts**:
   * Open the Swagger docs at `http://localhost:8000/docs`.
   * Execute `POST /api/v1/alerts/test-trigger` with company ID `C-1002` to confirm calculations and send WhatsApp notifications immediately.
   * Query `GET /api/v1/alerts/history` to review the delivery log records.

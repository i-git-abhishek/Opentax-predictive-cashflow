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

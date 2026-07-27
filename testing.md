# TESTING.md — Tally Integration (feature/tally-tdl)

This documents how to test the Team 1 (Tally Edge Integration) module end-to-end on
Windows, what currently works, and how it's meant to behave once fully wired to real
voucher-save events — including how TallyPrime Educational Mode's date restriction
(1st, 2nd, 31st only) fits into that.

## Prerequisites

- TallyPrime installed in **Educational Mode** (free — click "Try It For Free" instead
  of activating a license; confirm the green "EDU" tag is visible)
- A dummy company created inside Tally (any name/details)
- The backend running and reachable — either on the same Windows machine, or over
  LAN/ngrok if Tally is on Windows and the FastAPI server is on Linux
- `tally-tdl/opentax_daily_sync.tdl` downloaded onto the Windows machine

## Part 1 — What's implemented right now (Module 1)

Module 1 is a **static test**, not the real voucher-save hook yet. It adds a clickable
menu item to Tally that fires one fixed JSON payload to a webhook.site URL. Its only
purpose is proving the TDL → HTTP POST pipe itself works, before touching real ledger
data or the actual save event.

### How to test Module 1

1. Load the TDL file: `F4` → Manage Local TDLs → point to
   `opentax_daily_sync.tdl` → enable
2. Fully restart TallyPrime (TDL loads at startup)
3. Open [webhook.site](https://webhook.site) in a browser, keep the tab open
4. Paste that unique URL into the `OpenTaxWebhookURL` formula in the TDL file
   (if not already done), reload the TDL
5. On Gateway of Tally, click **"Test OpenTax Sync"** (appears near Quit)
6. Check the webhook.site tab — a POST request should appear with the payload

**Expected result:** one request lands on webhook.site. If nothing shows up, or Tally
throws a compile error on load, that's a Module 1 bug — check the TDL syntax before
moving to Part 2.

## Part 2 — What's _not_ built yet (the real hook)

Module 1 does not touch actual vouchers or ledgers. The real deliverable — not yet
written — needs to:

1. Hook the **"Voucher Save"** event on Sales/Purchase voucher forms (fires silently,
   no popup)
2. On save, aggregate the **running total for that day** across Sales and Purchase
   ledgers (not just the one voucher just saved — the cumulative total so far today)
3. Format that total into the real JSON contract:
   ```json
   {
     "company_id": "C-1002",
     "date": "YYYY-MM-DD",
     "daily_sales_tax": 4500.0,
     "daily_purchase_tax": 1500.0
   }
   ```
4. POST it to the real ingestion endpoint — `http://<backend-host>:8000/api/v1/ingest/daily-delta`
   — instead of webhook.site

This is the harder, unverified part (ledger naming conventions, `ALLLEDGERENTRIES.LIST`
traversal, hooking the actual save event) and should be built and tested as its own
follow-up module.

## Part 3 — How the 1st / 2nd / 31st restriction actually applies

**Important: this restriction affects your testing, not the real system's design.**

Educational Mode only lets you date a voucher as the 1st, 2nd, or 31st of a month — it
has nothing to do with the ingestion contract or the alert schedule. Two separate
things to keep straight:

- **Team 1's job (this module):** push a daily-delta payload _whenever a voucher is
  saved_, on whatever date that voucher happens to carry. It doesn't care what the
  calendar date is — any valid date works.
- **Team 3's job (unrelated to Tally):** fire the forecast alert on the 25th and the
  final-bill alert on the 1st, based on data already sitting in the database. This is
  tested entirely on the backend side via `SCHEDULER_INTERVAL_MINUTES` in `.env` — it
  never touches Tally or voucher dates at all.

So testing the real voucher-save hook is fully possible under Educational Mode's
restriction:

1. Create a Sales voucher dated the **1st** (or 2nd, or 31st) of any month
2. Save it — confirm the TDL hook fires and a payload lands on your ingestion endpoint
3. Check `opentax.db` (via DB Browser for SQLite) — confirm a row exists for that date
4. Save a **second** voucher on the same date — confirm the existing row updates
   (UPSERT) rather than duplicating, same as we verified for the Python side earlier

One deliberate design choice this relies on: the ingestion schema does **not** enforce
"date must be exactly today" at validation time — this was intentional (see
`schemas/tally_payload.py`), specifically to avoid clock-mismatch false rejections
between Tally's machine date and the server's. That choice means Educational Mode's
restricted dates won't get rejected by the backend — any valid date Tally allows will
be accepted and stored correctly.

## Part 4 — Full end-to-end proof (once Part 2 is built)

1. Save a voucher in Tally (dated 1st/2nd/31st) → confirm it lands in `opentax.db`
2. Hit `POST /api/v1/alerts/test-trigger` manually → confirm the WhatsApp alert
   (dry-run) reflects the real number that just came from Tally, not a hardcoded value
3. This proves the full chain: **Tally → ingestion → database → calculation →
   alert**, with only the calendar-driven cron timing (25th/1st) left unverified in
   Tally itself — which is expected, since that's Team 3's concern, not Team 1's.

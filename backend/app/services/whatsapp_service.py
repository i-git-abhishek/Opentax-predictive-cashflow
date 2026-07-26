import time
import logging
from datetime import date
from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger("whatsapp_service")
logging.basicConfig(level=logging.INFO)

def get_month_name(month_num: int) -> str:
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return months[month_num - 1]

def get_alert_message_body(alert_type: str, target_date: date, liability: float) -> str:
    """
    Formats the message body dynamically matching the exact wording requested in the Alert Contract.
    
    - Job A (FORECAST on the 25th of Month X):
      Calculates liability for Month X. Settled by 20th of Month X+1.
      "⚠️ OpenTax Alert: Based on your sales trajectory, your estimated GST liability for October is ₹45,000. Please ensure sufficient liquidity is provisioned before the 20th of November."
      
    - Job B (FINAL_SUMMARY on the 1st of Month X):
      Calculates liability for Month X-1. Settled by 20th of Month X.
      "📊 OpenTax Final Summary: Your finalized GST liability for October is ₹48,500. This amount must be settled by the 20th of November."
    """
    formatted_liability = f"₹{liability:,.2f}"

    if alert_type == "FORECAST":
        # Current month Name
        month_name = get_month_name(target_date.month)
        # Next month Name
        next_month_num = target_date.month + 1 if target_date.month < 12 else 1
        next_month_name = get_month_name(next_month_num)
        
        return (
            f"⚠️ OpenTax Alert: Based on your sales trajectory, your estimated GST liability "
            f"for {month_name} is {formatted_liability}. Please ensure sufficient liquidity "
            f"is provisioned before the 20th of {next_month_name}."
        )
    elif alert_type == "FINAL_SUMMARY":
        # Previous month Name
        prev_month_num = target_date.month - 1 if target_date.month > 1 else 12
        prev_month_name = get_month_name(prev_month_num)
        # Current month Name (where payment is due)
        curr_month_name = get_month_name(target_date.month)
        
        return (
            f"📊 OpenTax Final Summary: Your finalized GST liability "
            f"for {prev_month_name} is {formatted_liability}. This amount must be "
            f"settled by the 20th of {curr_month_name}."
        )
    else:
        return f"OpenTax Notification: Your GST liability is {formatted_liability}."

def send_whatsapp_message(to_number: str, body: str) -> dict:
    """
    Dispatches WhatsApp messages via Twilio API with exponential backoff retry.
    Returns a status dict containing delivery report and retry count.
    """
    # Enforce standard formatting
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"
        
    from_number = settings.TWILIO_FROM_WHATSAPP_NUMBER
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    # Dry-run fallback mode if credentials are empty
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("[DRY-RUN Fallback] Twilio credentials are missing in environment.")
        logger.info(f"[DRY-RUN Output] Sending message to: {to_number}")
        logger.info(f"[DRY-RUN Output] Body: {body}")
        return {
            "status": "SENT_DRY_RUN",
            "retry_count": 0,
            "error_message": None
        }

    max_retries = 3
    backoff = 1.0 # Base sleep time in seconds

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempting to send WhatsApp message via Twilio (Attempt {attempt})...")
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=body,
                from_=from_number,
                to=to_number
            )
            logger.info(f"Message sent successfully. SID: {message.sid}")
            return {
                "status": "SENT",
                "retry_count": attempt,
                "error_message": None
            }
        except Exception as e:
            logger.warning(f"Error on attempt {attempt}: {str(e)}")
            if attempt == max_retries:
                logger.error("Max retries reached. Failing alert delivery.")
                return {
                    "status": "FAILED",
                    "retry_count": attempt,
                    "error_message": str(e)
                }
            time.sleep(backoff)
            backoff *= 2.0 # Exponential backoff

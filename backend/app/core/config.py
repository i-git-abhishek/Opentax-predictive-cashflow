import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./opentax.db")

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str | None = Field(default=None)
    TWILIO_AUTH_TOKEN: str | None = Field(default=None)
    TWILIO_FROM_WHATSAPP_NUMBER: str = Field(default="whatsapp:+14155238886") # Default Twilio Sandbox Number
    DEFAULT_TO_WHATSAPP_NUMBER: str = Field(default="whatsapp:+919876543210") # User's WhatsApp number

    # Company Defaults
    DEFAULT_COMPANY_ID: str = Field(default="C-1002")

    # Testing / Debug Configuration
    SCHEDULER_INTERVAL_MINUTES: int | None = Field(default=None) # Set to an integer to override the monthly cron with a minutely frequency for testing

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

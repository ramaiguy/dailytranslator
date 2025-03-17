import os
from pathlib import Path


class Config:
    """Configuration settings for the translation service."""
    
    # Application paths
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = os.path.join(BASE_DIR, "data")
    TEXTS_DIR = os.path.join(DATA_DIR, "texts")
    TRANSLATED_DIR = os.path.join(DATA_DIR, "translated")
    
    # Email configuration
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.example.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "translation_service@example.com")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = True
    REPLY_TO_EMAIL = os.environ.get("REPLY_TO_EMAIL", "translations@example.com")
    
    # SMS configuration (if using a service like Twilio)
    SMS_ACCOUNT_SID = os.environ.get("SMS_ACCOUNT_SID", "")
    SMS_AUTH_TOKEN = os.environ.get("SMS_AUTH_TOKEN", "")
    SMS_FROM_NUMBER = os.environ.get("SMS_FROM_NUMBER", "")
    
    # Application settings
    DEFAULT_SENTENCES_PER_DAY = 3
    SEND_TIME_HOUR = 8  # Send at 8 AM by default
    MAX_SENTENCE_LENGTH = 200  # Maximum length of a sentence in characters
    
    # Ensure required directories exist
    @classmethod
    def create_directories(cls):
        """Create required directories if they don't exist."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.TEXTS_DIR, exist_ok=True)
        os.makedirs(cls.TRANSLATED_DIR, exist_ok=True)


# Create directories when module is imported
Config.create_directories()

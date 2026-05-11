import os
import json
from pathlib import Path

# Try to load config from JSON file if it exists (backwards compatibility)
config = {}
config_file = Path(__file__).parent.parent / 'config.json'
if config_file.exists():
    with open(config_file, 'r') as f:
        config = json.loads(f.read())


class Config:
    """
    Flask configuration class.
    Supports environment variables (preferred) with fallback to config.json.

    Environment variables take precedence over config.json values.
    """
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', config.get('SECRET_KEY'))

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        config.get('SQLALCHEMY_DATABASE_URI')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Suppress warning

    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', config.get('MAIL_SERVER'))
    MAIL_PORT = int(os.getenv('MAIL_PORT', config.get('MAIL_PORT', 587)))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', str(config.get('MAIL_USE_TLS', True))).lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', config.get('MAIL_USERNAME'))
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', config.get('MAIL_PASSWORD'))
    EMAIL_NAME = os.getenv('EMAIL_NAME', config.get('EMAIL_NAME', 'AHmaths'))
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', config.get('EMAIL_ADDRESS', config.get('MAIL_USERNAME')))

    # reCAPTCHA
    RECAPTCHA_SECRET = os.getenv('RECAPTCHA_SECRET', config.get('RECAPTCHA_SECRET'))
    RECAPTCHA_SITEKEY = os.getenv('RECAPTCHA_SITEKEY', config.get('RECAPTCHA_SITEKEY'))

    # Contact form recipient (defaults to EMAIL_ADDRESS / MAIL_USERNAME)
    CONTACT_RECIPIENT = os.getenv('CONTACT_RECIPIENT', config.get('CONTACT_RECIPIENT'))

    # Analytics
    GA_MEASUREMENT_ID = os.getenv('GA_MEASUREMENT_ID', config.get('GA_MEASUREMENT_ID'))

    # Session / cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv(
        'SESSION_COOKIE_SECURE',
        str(config.get('SESSION_COOKIE_SECURE', True)),
    ).lower() in ('true', '1', 'yes')
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

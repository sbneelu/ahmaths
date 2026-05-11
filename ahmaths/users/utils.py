import logging

import requests
from flask import url_for, current_app
from flask_mail import Message

from ahmaths import mail

log = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


def send_reset_password_email(user):
    token = user.get_reset_token(expires_seconds=86400)
    sender_name = current_app.config.get('EMAIL_NAME', 'AHmaths')
    sender_address = current_app.config.get(
        'EMAIL_ADDRESS', current_app.config.get('MAIL_USERNAME')
    )
    msg = Message(
        'Reset your Password (AHmaths.com)',
        sender=(sender_name, sender_address),
        recipients=[user.email],
    )
    msg.body = f'''A password reset has been requested for your account. Please go to the following link to reset your password:
{url_for('users.reset_password', token=token, _external=True)}

This link is valid for 24 hours.


If you did not request a password reset you do not need to do anything, and no changes will be made.'''
    mail.send(msg)


def verify_recaptcha(response_token):
    """Verify a reCAPTCHA token. Returns an error string for the user, or None on success.

    Skips verification (returns None) when no secret is configured or in testing mode,
    so local/dev/test environments don't need to wire up a real reCAPTCHA secret.
    """
    secret = current_app.config.get('RECAPTCHA_SECRET')
    if not secret or current_app.config.get('TESTING'):
        return None
    if not response_token:
        return 'Please fill out the Captcha.'
    try:
        resp = requests.post(
            RECAPTCHA_VERIFY_URL,
            data={'secret': secret, 'response': response_token},
            timeout=5,
        )
        resp.raise_for_status()
        if resp.json().get('success'):
            return None
    except requests.RequestException:
        log.warning('reCAPTCHA verification failed to reach Google', exc_info=True)
        return 'Could not verify Captcha. Please try again.'
    return 'Invalid Captcha. Please try again.'

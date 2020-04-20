from flask import url_for
from flask_mail import Message
from ahmaths import mail
from ahmaths.config import config


def send_reset_password_email(user):
    token = user.get_reset_token(86400)
    msg = Message('Reset your Password (AHmaths.com)', sender=(config['EMAIL_NAME'], config['EMAIL_ADDRESS']), recipients=[user.email])
    msg.body = f'''A password reset has been requested for your account. Please go to the following link to reset your password:
{url_for('users.reset_password', token=token, _external=True)}

This link is valid for 24 hours.


If you did not request a password reset you do not need to do anything, and no changes will be made.'''
    mail.send(msg)

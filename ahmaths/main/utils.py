from flask import current_app
from flask_mail import Message
from ahmaths import mail


def send_contact_email(name, email, subject, message):
    sender_name = current_app.config.get('EMAIL_NAME', 'AHmaths')
    sender_address = current_app.config.get(
        'EMAIL_ADDRESS', current_app.config.get('MAIL_USERNAME')
    )
    recipient = current_app.config.get('CONTACT_RECIPIENT') or sender_address
    msg = Message(
        f'AHmaths.com - {subject}',
        sender=(sender_name, sender_address),
        recipients=[recipient],
    )
    msg.body = f'''Sender: {name} <{email}>
Subject: {subject}

Message:
{message}
'''
    mail.send(msg)

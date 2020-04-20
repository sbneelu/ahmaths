from flask_mail import Message
from ahmaths import mail
from ahmaths.config import config


def send_contact_email(name, email, subject, message):
    msg = Message('AHmaths.com - ' + subject, sender=(config['EMAIL_NAME'], config['EMAIL_ADDRESS']), recipients=['neelu.rsa@gmail.com'])
    msg.body = f'''Sender: {name} <{email}>
Subject: {subject}

Message:
{message}
'''
    mail.send(msg)

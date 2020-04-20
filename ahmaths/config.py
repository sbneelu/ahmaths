import json

with open('config.json', 'r') as f:
    config_file = f.read()
    config = json.loads(config_file)


class Config:
    SECRET_KEY = config['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = config['SQLALCHEMY_DATABASE_URI']
    MAIL_SERVER = config['MAIL_SERVER']
    MAIL_PORT = config['MAIL_PORT']
    MAIL_USE_TLS = config['MAIL_USE_TLS']
    MAIL_USERNAME = config['MAIL_USERNAME']
    MAIL_PASSWORD = config['MAIL_PASSWORD']
    RECAPTCHA_SECRET = config['RECAPTCHA_SECRET']
    RECAPTCHA_SITEKEY = config['RECAPTCHA_SITEKEY']

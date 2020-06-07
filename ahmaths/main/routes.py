from flask import render_template, url_for, redirect, flash, Blueprint, request
from flask_login import current_user
from ahmaths.main.forms import ContactForm
from ahmaths.main.utils import send_contact_email
import requests
from ahmaths.config import Config

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('main/index.html.j2')


@main.route('/home')
def home():
    if current_user.is_authenticated:
        return render_template('main/home.html.j2')
    return redirect(url_for('main.index'))


@main.route('/contact', methods=['GET', 'POST'])
def contact():
    captcha_error = None
    form = ContactForm()
    if form.validate_on_submit():
        if not request.form.get('g-recaptcha-response'):
            captcha_error = 'Please fill out the Captcha.'
            return render_template('main/contact.html.j2', title="Contact/Report a Problem", form=form, captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)
        payload = {
            'secret': Config.RECAPTCHA_SECRET,
            'response': request.form.get('g-recaptcha-response')
        }

        success = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload).json()['success']
        if not success:
            captcha_error = 'Invalid Captcha. Please try again.'
            return render_template('main/contact.html.j2', title="Contact/Report a Problem", form=form, captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)
        send_contact_email(form.name.data, form.email.data, form.subject.data, form.message.data)
        flash('Your message has been sent.', 'info')
        return redirect(url_for('main.home'))
    return render_template('main/contact.html.j2', title="Contact/Report a Problem", form=form, captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)

@main.route('/loaderio-c9d2c576953e1187f67621f069d2c6aa.html')
def loaderio():
    return 'loaderio-c9d2c576953e1187f67621f069d2c6aa'

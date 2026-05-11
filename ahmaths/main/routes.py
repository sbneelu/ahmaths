from flask import render_template, url_for, redirect, flash, Blueprint, request, current_app
from flask_login import current_user

from ahmaths.main.forms import ContactForm
from ahmaths.main.utils import send_contact_email
from ahmaths.users.utils import verify_recaptcha

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
    form = ContactForm()
    captcha_error = None
    if form.validate_on_submit():
        captcha_error = verify_recaptcha(request.form.get('g-recaptcha-response'))
        if captcha_error is None:
            send_contact_email(
                form.name.data, form.email.data, form.subject.data, form.message.data
            )
            flash('Your message has been sent.', 'info')
            return redirect(url_for('main.home'))
    return render_template(
        'main/contact.html.j2',
        title='Contact/Report a Problem',
        form=form,
        captcha_error=captcha_error,
        captcha_sitekey=current_app.config.get('RECAPTCHA_SITEKEY'),
    )


@main.route('/loaderio-c9d2c576953e1187f67621f069d2c6aa.html')
def loaderio():
    return 'loaderio-c9d2c576953e1187f67621f069d2c6aa'

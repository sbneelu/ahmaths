from flask import render_template, url_for, redirect, flash, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from ahmaths import bcrypt, db
from ahmaths.models import User, Topic
from ahmaths.users.forms import SignupForm, LoginForm, RequestResetPasswordForm, ResetPasswordForm, UpdateEmailForm, UpdatePasswordForm
from ahmaths.users.utils import send_reset_password_email
from ahmaths.users.delete_progress import delete_topic_progress
from ahmaths.config import Config
import requests

users = Blueprint('users', __name__)


@users.route('/signup', methods=['GET', 'POST'])
def signup():
    captcha_error = None
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = SignupForm()
    if form.validate_on_submit():
        if not request.form.get('g-recaptcha-response'):
            captcha_error = 'Please fill out the Captcha.'
            return render_template('users/signup.html.j2', form=form, title='Sign Up', captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)
        payload = {
            'secret': Config.RECAPTCHA_SECRET,
            'response': request.form.get('g-recaptcha-response')
        }

        success = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload).json()['success']
        if not success:
            captcha_error = 'Invalid Captcha. Please try again.'
            return render_template('users/signup.html.j2', form=form, title='Sign Up', captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.home'))
    form.validate_on_submit()
    return render_template('users/signup.html.j2', form=form, title='Sign Up', captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check your email address and password.', 'danger')
    return render_template('users/login.html.j2', form=form, title='Login')


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@users.route('/reset_password', methods=['GET', 'POST'])
def request_reset_password():
    captcha_error = None
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        if not request.form.get('g-recaptcha-response'):
            captcha_error = 'Please fill out the Captcha.'
            return render_template('users/request_reset_password.html.j2', title='Reset Password', form=form, captcha_error = captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)
        payload = {
            'secret': Config.RECAPTCHA_SECRET,
            'response': request.form.get('g-recaptcha-response')
        }

        success = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload).json()['success']
        if not success:
            captcha_error = 'Invalid Captcha. Please try again.'
            return render_template('users/request_reset_password.html.j2', title='Reset Password', form=form, captcha_error = captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_password_email(user)
        flash(f'Instructions to reset your password have been sent to your email address. If you have not received an email within 5 minutes, please check your spam folder or try requesting a password reset again or report in on the <a class="alert-link" href="{url_for("main.contact")}">Contact/Report a Problem</a> page.', 'info')
        return redirect(url_for('users.login'))
    return render_template('users/request_reset_password.html.j2', title='Reset Password', form=form, captcha_error=captcha_error, captcha_sitekey=Config.RECAPTCHA_SITEKEY)


@users.route('/reset_password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Invalid or expired password reset link. Please request another password reset link.', 'warning')
        return redirect(url_for('users.request_reset_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been reset. You may now use your new password to log in to your account.', 'info')
        return redirect(url_for('users.login'))
    return render_template('users/reset_password.html.j2', title='Reset Password', form=form)


@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateEmailForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash('Your email address has been updated.', 'info')
    form.email.data = form.email.data or current_user.email
    topics = Topic.query.all()
    return render_template('users/account.html.j2', form=form, topics=topics, title='Account')


@users.route('/account/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        current_user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated.', 'info')
        return redirect(url_for('users.account'))
    return render_template('users/update_password.html.j2', form=form, title='Update Password')


@users.route('/account/confirm_delete_progress/<path:topic_id>')
@login_required
def confirm_delete_progress(topic_id):
    if not Topic.query.filter_by(topic_id=topic_id).first() and topic_id != 'all':
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('users.account'))
    topic = Topic.query.filter_by(topic_id=topic_id).first()
    topic_name = 'All' if topic_id == 'all' else topic.topic_name
    return render_template('users/confirm_delete_progress.html.j2', topic_name=topic_name, topic_id=topic_id, title='Delete Progress')


@users.route('/account/delete_progress/<path:topic_id>')
@login_required
def delete_progress(topic_id):
    if not Topic.query.filter_by(topic_id=topic_id).first() and topic_id != 'all':
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('users.account'))

    if topic_id == 'all':
        topics = Topic.query.all()
        for topic in topics:
            setattr(current_user, topic.topic_id, '')
        setattr(current_user, 'progress', 'partial_fractions:0,binomial_theorem:0,differentiation:0,integration:0,differential_equations:0,functions_graphs:0,systems_of_equations:0,complex_numbers:0,sequences_series:0,maclaurin_series:0,matrices:0,vectors:0,methods_of_proof:0,number_theory:0')
        db.session.commit()
        flash('All progress has been deleted successfully.', 'info')
    else:
        delete_topic_progress(topic_id)
        flash(f'All progress for {Topic.query.filter_by(topic_id=topic_id).first().topic_name} has been deleted successfully.', 'info')
    return redirect(url_for('users.account'))

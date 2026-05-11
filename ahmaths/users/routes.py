from flask import render_template, url_for, redirect, flash, request, Blueprint, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from ahmaths import bcrypt, db
from ahmaths.models import User, Topic
from ahmaths.users.forms import (
    SignupForm, LoginForm, RequestResetPasswordForm, ResetPasswordForm,
    UpdateEmailForm, UpdatePasswordForm,
)
from ahmaths.users.utils import send_reset_password_email, verify_recaptcha
from ahmaths.users.delete_progress import delete_topic_progress

users = Blueprint('users', __name__)


DEFAULT_PROGRESS = (
    'partial_fractions:0,binomial_theorem:0,differentiation:0,integration:0,'
    'differential_equations:0,functions_graphs:0,systems_of_equations:0,'
    'complex_numbers:0,sequences_series:0,maclaurin_series:0,matrices:0,'
    'vectors:0,methods_of_proof:0,number_theory:0'
)


def _is_safe_redirect_target(target):
    """Allow only relative redirects to prevent open-redirect attacks."""
    if not target:
        return False
    if any(c in target for c in '\\\r\n\t'):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc and target.startswith('/')


def _hash_password(plain):
    hashed = bcrypt.generate_password_hash(plain)
    if isinstance(hashed, bytes):
        hashed = hashed.decode('utf-8')
    return hashed


@users.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = SignupForm()
    captcha_error = None
    if form.validate_on_submit():
        captcha_error = verify_recaptcha(request.form.get('g-recaptcha-response'))
        if captcha_error is None:
            user = User(email=form.email.data, password=_hash_password(form.password.data))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('main.home'))
    return render_template(
        'users/signup.html.j2', form=form, title='Sign Up',
        captcha_error=captcha_error,
        captcha_sitekey=current_app.config.get('RECAPTCHA_SITEKEY'),
    )


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
            if _is_safe_redirect_target(next_page):
                return redirect(next_page)
            return redirect(url_for('main.home'))
        flash('Login unsuccessful. Please check your email address and password.', 'danger')
    return render_template('users/login.html.j2', form=form, title='Login')


@users.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@users.route('/reset_password', methods=['GET', 'POST'])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetPasswordForm()
    captcha_error = None
    if form.validate_on_submit():
        captcha_error = verify_recaptcha(request.form.get('g-recaptcha-response'))
        if captcha_error is None:
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None:
                send_reset_password_email(user)
            # Always show the same message — do not leak account existence.
            flash(
                'If an account exists for that email, instructions to reset your password '
                'have been sent. If you have not received an email within 5 minutes, please '
                'check your spam folder or report it on the '
                f'<a class="alert-link" href="{url_for("main.contact")}">'
                'Contact/Report a Problem</a> page.',
                'info',
            )
            return redirect(url_for('users.login'))
    return render_template(
        'users/request_reset_password.html.j2', title='Reset Password', form=form,
        captcha_error=captcha_error,
        captcha_sitekey=current_app.config.get('RECAPTCHA_SITEKEY'),
    )


@users.route('/reset_password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token, max_age=86400)
    if user is None:
        flash('Invalid or expired password reset link. Please request another password reset link.', 'warning')
        return redirect(url_for('users.request_reset_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = _hash_password(form.password.data)
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
        current_user.password = _hash_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated.', 'info')
        return redirect(url_for('users.account'))
    return render_template('users/update_password.html.j2', form=form, title='Update Password')


@users.route('/account/confirm_delete_progress/<path:topic_id>')
@login_required
def confirm_delete_progress(topic_id):
    if topic_id != 'all' and not Topic.query.filter_by(topic_id=topic_id).first():
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('users.account'))
    topic = Topic.query.filter_by(topic_id=topic_id).first()
    topic_name = 'All' if topic_id == 'all' else topic.topic_name
    return render_template(
        'users/confirm_delete_progress.html.j2',
        topic_name=topic_name, topic_id=topic_id, title='Delete Progress',
    )


@users.route('/account/delete_progress/<path:topic_id>', methods=['POST'])
@login_required
def delete_progress(topic_id):
    if topic_id != 'all' and not Topic.query.filter_by(topic_id=topic_id).first():
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('users.account'))

    if topic_id == 'all':
        topics = Topic.query.all()
        for topic in topics:
            setattr(current_user, topic.topic_id, '')
        current_user.progress = DEFAULT_PROGRESS
        db.session.commit()
        flash('All progress has been deleted successfully.', 'info')
    else:
        delete_topic_progress(topic_id)
        topic_name = Topic.query.filter_by(topic_id=topic_id).first().topic_name
        flash(f'All progress for {topic_name} has been deleted successfully.', 'info')
    return redirect(url_for('users.account'))

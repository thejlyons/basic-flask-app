"""Auth Endpoints."""
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm, UnsubscribeForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_password_reset, send_confirm_email
from app.models import db, User, Unsubscriber
import app.tools as tools


@bp.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    """Unsubscribe endpoint."""
    form = UnsubscribeForm()
    return render_template('auth/unsubscribe.html', title="Unsubscribe", form=form)


@bp.route('/unsubscribe/submit', methods=['POST'])
def unsubscribe_submit():
    """Unsubscribe endpoint."""
    form = UnsubscribeForm()
    if form.validate_on_submit():
        unsub = Unsubscriber(email=form.email.data)
        db.session.add(unsub)
        db.session.commit()
        flash("Your email and preferences have been recorded..")
    return redirect(url_for('auth.unsubscribe'))


@bp.route('/login', methods=['GET'])
def login():
    """Login endpoint."""
    token = request.args.get('token')
    if token:
        user = User.verify_confirm_email_token(token)
        if user:
            user.email_confirmed = True
            db.session.commit()
            flash("Thank you. Your email has been confirmed!")
            redirect(user.get_landing_page())
        else:
            flash("You're confirmation link is invalid.")
    if current_user.is_authenticated:
        return redirect(current_user.get_landing_page())
    form = LoginForm()
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/login/submit', methods=['POST'])
def login_submit():
    """Login endpoint."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get(email=form.email.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
        else:
            login_user(user, remember=form.remember_me.data)
            flash("Logged in!")
            return redirect(user.get_landing_page())
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET'])
def register():
    """Login endpoint."""
    if current_user.is_authenticated:
        return redirect(current_user.get_landing_page())
    form = RegisterForm()
    return render_template('auth/register.html', title='Sign In', form=form)


@bp.route('/register/submit', methods=['POST'])
def register_submit():
    """Login endpoint."""
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.get(email=form.email.data)
        if user:
            flash('That email is already taken')
        else:
            user = User(email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            send_confirm_email(user)
            login_user(user)
            flash("Registered!")
            return redirect(user.get_landing_page())
    return render_template('auth/register.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    """Logout endpoint."""
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('index'))


@bp.route('/reset_password_request', methods=['GET'])
def reset_password_request():
    """Request Password Reset endpoint."""
    if current_user.is_authenticated:
        flash("Already logged in!")
        return redirect(current_user.get_landing_page())
    form = ResetPasswordRequestForm()
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


@bp.route('/reset_password_request/submit', methods=['POST'])
def reset_password_request_submit():
    """Request Password Reset Submit endpoint."""
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.get(email=form.email.data)
        if user:
            send_password_reset(user)
            flash('Check your email for the instructions to reset your password')
            return redirect(url_for('auth.login'))
        else:
            flash('There is no user associated with that email. Please try again.')
    return redirect(url_for('auth.reset_password_request'))


@bp.route('/reset_password/<token>', methods=['GET'])
def reset_password(token):
    """Reset Password."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Your reset link has expired. Please request a new one.')
        return redirect(url_for('auth.reset_password_request'))
    form = ResetPasswordForm()
    return render_template('auth/reset_password.html', title='Reset Password', form=form, token=token)


@bp.route('/reset_password/submit/<token>', methods=['POST'])
def reset_password_submit(token):
    """Reset Password Submit."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Your reset link has expired. Please request a new one.')
        return redirect(url_for('auth.reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        login_user(user, remember=False)
        return redirect(user.get_landing_page())
    return redirect(url_for('auth.reset_password_request', token=token))

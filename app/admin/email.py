"""Admin Emails."""
from flask import render_template
from app.email import send_email


def send_confirm_email(user):
    """Send Confirm Email Request."""
    token = user.get_confirm_email_token()
    subject = "Confirm Email"
    html_body = render_template('emails/confirm_email.html', user=user, token=token)
    send_email(user.email, subject, html_body)


def send_password_reset(user):
    """Send Password Reset."""
    token = user.get_reset_password_token()
    subject = "Password Reset"
    html_body = render_template('emails/reset_password.html', user=user, token=token)
    send_email(user.email, subject, html_body)

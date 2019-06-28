"""Send email methods."""
import os
from threading import Thread
from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, MailSettings, SandBoxMode


def send_async_email(app, email_info):
    """Send an email."""
    with app.app_context():
        from_email = Email(email=os.environ.get("EMAIL_ADDR"), name=os.environ.get("EMAIL_NAME", ""))
        message = Mail(from_email=from_email, to_emails=email_info['to_email'], subject=email_info['subject'],
                       html_content=email_info['content'])

        if app.config.get('TESTING'):
            sbm = SandBoxMode(True)
            message.mail_settings = MailSettings(sandbox_mode=sbm)
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            if app.config.get('TESTING') and response.status_code != 200:
                raise Exception("Could not send email:\n{}".format(message.get()))
            elif not app.config.get('TESTING') and response.status_code != 202:
                app.logger.error("Could not send email:\n{}".format(message.get()))
        except Exception as e:
            app.logger.error("Error sending email: \n{}".format(e))


def send_email(to_email, subject, html_body):
    """Generate email Thread with given information."""
    email_info = {
        'to_email': to_email,
        'subject': subject,
        'content': html_body
    }
    Thread(target=send_async_email, args=(current_app._get_current_object(), email_info)).start()

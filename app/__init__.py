import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import boto3
import sendgrid
from sendgrid.helpers.mail import *
from flask_sslify import SSLify

app = Flask(__name__, static_url_path='/static')
app.config.from_object(os.environ['APP_SETTINGS'])

# TODO: Add Celery
# TODO: Separate .flaskenv (pushable) and .env (private) env vars.
# TODO: Add custom error messaging for push notifications to error logging app.

sslify = SSLify(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'auth.login'
s3 = boto3.client("s3", aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
                  aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"))


from app import models, routes
from app.auth import bp as auth_bp
app.register_blueprint(auth_bp)


class EmailHandler(logging.Handler):
    """Custom error handler for sending error print out emails to devs."""

    def emit(self, record):
        """Generate email."""
        log_entry = self.format(record)
        body = '<pre>{}</pre><br><br><a href="https://meetgessi.com/unsubscribe">Unsubscribe</a>'.format(log_entry)
        sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
        email_obj = Mail(Email(os.environ.get("EMAIL_ADDR"), os.environ.get("EMAIL_NAME", "")),
                         '{} [Error]'.format(os.environ.get("ENV_NAME", "ENV Not Set")), Email('j@jlyons.me'),
                         Content('text/html', body))
        response = sg.client.mail.send.post(request_body=email_obj.get())


# Setup debug
if not app.debug:
    email_handler = EmailHandler()
    email_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    email_handler.setLevel(logging.ERROR)
    app.logger.addHandler(email_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Site startup')

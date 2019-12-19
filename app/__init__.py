import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from celery import Celery
import boto3
import sendgrid
from sendgrid.helpers.mail import *
from flask_sslify import SSLify
from dotenv import load_dotenv


if not os.environ.get('APP_SETTINGS'):
    load_dotenv('.flaskenv')

app = Flask(__name__, static_url_path='/static')
app.config.from_object(os.environ['APP_SETTINGS'])


celery = Celery(
    app.import_name,
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)


class ContextTask(celery.Task):
    """Celery Context Task Class."""
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

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

from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app import cli
app.cli.add_command(cli.user_cli)
app.cli.add_command(cli.manage_cli)


class EmailHandler(logging.Handler):
    """Custom error handler for sending error print out emails to devs."""

    def emit(self, record):
        """Generate email."""
        log_entry = self.format(record)
        body = '<pre>{}</pre><br><br><a href="https://meetgessi.com/unsubscribe">Unsubscribe</a>'.format(log_entry)
        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        from_email = Email(email=os.environ.get("EMAIL_ADDR"), name=os.environ.get("EMAIL_NAME", ""))
        message = Mail(from_email=from_email, to_emails=os.environ['ADMIN_EMAILS'],
                       subject='{} [Error]'.format(os.environ.get("ENV_NAME", "ENV Not Set")), html_content=body)
        response = sg.send(message)


# Setup debug
if not app.debug:
    email_handler = EmailHandler()
    email_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    email_handler.setLevel(logging.ERROR)
    app.logger.addHandler(email_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Site startup')

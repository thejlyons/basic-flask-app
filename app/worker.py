import click
from app.models import db, User
from flask.cli import AppGroup

user_cli = AppGroup('user')


@user_cli.command('make-admin')
@click.argument('email')
def inactive_user(email):
    """Make user admin."""
    user = User.query.filter_by(email=email).first()
    if user:
        user.admin = True
        db.session.commit()

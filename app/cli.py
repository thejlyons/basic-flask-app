"""CLI Methods."""
import sass
import click
from app import app
from pathlib import Path
from app.models import db, User
from flask.cli import AppGroup

user_cli = AppGroup('user', help="Useful commands for managing users")
manage_cli = AppGroup('manage')


@user_cli.command('make-admin')
@click.argument('email')
def inactive_user(email):
    """Make user admin."""
    user = User.query.filter_by(email=email).first()
    if user:
        user.admin = True
        db.session.commit()


@user_cli.command('view')
@click.option('--id', '-i', 'id')
@click.option('--email', '-e', 'email')
def inactive_user(id=None, email=None):
    """Make user admin."""
    user = User.get(id=id, email=email)
    app.logger.debug(user)


@manage_cli.command('make-css')
def generate_css():
    """Generate CSS from SASS."""
    path_assets = Path.cwd() / 'app' / 'assets' / 'scss'
    path_css = Path.cwd() / 'app' / 'static' / 'css'
    if not path_css.exists():
        path_css.mkdir(parents=True, exist_ok=True)
    if not path_assets.exists():
        app.logger.error("Could not find app/assets/scss. Are you sure you're in the project root?")
    else:
        sass.compile(dirname=(path_assets, path_css), output_style='compressed')
        with open(path_css / 'bootstrap.css', 'w+') as css_out:
            print(css_out.read())
        app.logger.info("SASS has been compiled and the output can be found in app/static/css/custom.css")

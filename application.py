"""Pass360 App."""
from app import app as application
from app.models import db, User, Unsubscriber


@application.shell_context_processor
def make_shell_context():
    """Setup shell context for DB management."""
    return {'db': db, 'User': User, 'Unsubcriber': Unsubscriber}


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)

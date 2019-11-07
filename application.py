"""Basic App."""
from app import app, db
from app.models import User, Unsubscriber


@app.shell_context_processor
def make_shell_context():
    """Setup shell context for DB management."""
    return {'db': db, 'User': User, 'Unsubcriber': Unsubscriber}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

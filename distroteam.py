"""DistroTeam."""
import os
from dotenv import load_dotenv


# env_path = 'C:\\Users\\lyons\\Github\\distroteam\\.flaskenv'
# if os.path.exists(env_path):
#     load_dotenv(dotenv_path=env_path)

from app import app, db
from app.models import User


@app.shell_context_processor
def make_shell_context():
    """Setup shell context for DB management."""
    return {'db': db, 'User': User}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

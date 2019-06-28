"""Models."""
from flask_login import UserMixin
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from time import time
import os


@login.user_loader
def load_user(user_id):
    """Retrieve individual on login success."""
    individual = User.query.get(int(user_id))
    return individual


class User(UserMixin, db.Model):
    """
    User.

    Object for each account.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    email_confirmed = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    password_hash = db.Column(db.String(128))

    admin = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    influencer = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    def get_name(self):
        """Get name."""
        return self.email

    def set_password(self, password):
        """Set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password."""
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        """Generate password token."""
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, os.environ['SECRET_KEY'],
                          algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        """Verify reset password token."""
        try:
            user_id = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except (DecodeError, ExpiredSignatureError):
            return
        return User.query.get(user_id)

    def get_confirm_email_token(self, expires_in=259200):
        """Generate password token."""
        return jwt.encode({'confirm_email': self.id, 'exp': time() + expires_in}, os.environ['SECRET_KEY'],
                          algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_confirm_email_token(token):
        """Verify confirm email token."""
        try:
            user_id = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=['HS256'])['confirm_email']
        except (DecodeError, ExpiredSignatureError):
            return
        return User.query.get(user_id)


class Unsubscriber(db.Model):
    """
    Unsubscriber.

    Keeping track of emails that have requested to unsubscribe.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))

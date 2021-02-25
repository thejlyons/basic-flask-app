"""Auth unit tests."""
from flask_testing import TestCase
from flask import Flask, url_for
import os
from app import app
from app.models import db, User
import unittest
from unittest import mock

basedir = os.path.abspath(os.path.dirname(__file__))


class AuthTests(TestCase):
    """Unit Tests"""

    def create_app(self):
        app.config.from_object("config.TestingConfig")
        return app

    def setUp(self):
        """Set up."""
        self.tearDown()

        db.create_all()

        self.create_user()

    def tearDown(self):
        """Tear down."""
        db.session.remove()
        db.drop_all()

    """Login"""
    def test_login(self):
        """Test root loads."""
        with self.client:
            response = self.client.get(url_for('auth.login'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_login_valid_login(self):
        with self.client:
            response = self.client.post(
                url_for('auth.login_submit'),
                data=dict(email=self.user.email, password=self.password, submit="Sign In"),
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200, 'Could not login.')
            self.assertIn(b'Logged in!', response.data)

    def test_login_invalid_login(self):
        with self.client:
            response = self.client.post(
                url_for('auth.login_submit'),
                data=dict(email=self.user.email, password='asdf', submit="Sign In"),
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Invalid email or password', response.data)

    """Register"""
    def test_register(self):
        """Test root loads."""
        with self.client:
            response = self.client.get(url_for('auth.register'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_register_valid_registration(self):
        with self.client:
            email = 'j+register@jlyons.me'
            password = 'register'
            response = self.client.post(
                url_for('auth.register_submit'),
                data=dict(email=email, password=password, password2=password, submit='Register'),
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            user = User.query.filter_by(email=email).first()
            self.assertIsNotNone(user, 'User not created')
            self.assertTrue(user.check_password(password), 'Password does not match')

    def test_register_valid_confirm_email(self):
        with self.client:
            token = self.user.get_confirm_email_token()
            response = self.client.get(
                url_for('auth.login', token=token),
                follow_redirects=True
            )
            self.assertIn(b'Thank you. Your email has been confirmed!', response.data)
            self.assertTrue(self.user.email_confirmed)

    def test_register_invalid_confirm_email(self):
        with self.client:
            response = self.client.get(
                url_for('auth.login', token='fake-token'),
                follow_redirects=True
            )
            self.assertIn(b'confirmation link is invalid.', response.data)

    def test_register_invalid_duplicate_email(self):
        with self.client:
            response = self.client.post(
                url_for('auth.register_submit'),
                data=dict(email=self.user.email, password='invalid', password2='invalid', submit='Register'),
                follow_redirects=True
            )
            self.assertIn(b'That email is already taken', response.data)
            self.assertEqual(User.query.filter_by(email=self.user.email).count(), 1)

    def test_invalid_user_registration_passwords(self):
        with self.client:
            response = self.client.post(
                url_for('auth.register_submit'),
                data=dict(email='j+fail@jlyons.me', password='testing', password2='invalid', submit='Register'),
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Passwords must match', response.data)
            self.assertEqual(User.query.filter_by(email='j+fail@jlyons.me').count(), 0)

    """Reset Password Request"""
    def test_reset_password_request(self):
        """Test root loads."""
        with self.client:
            response = self.client.get(url_for('auth.reset_password_request'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Reset Password', response.data)

    def test_reset_password_request_valid(self):
        with self.client:
            response = self.client.post(
                url_for('auth.reset_password_request_submit'),
                data=dict(email=self.user.email, submit='Request Reset'),
                follow_redirects=True
            )
            self.assertIn(b'Check your email for the instructions to reset your password', response.data)

    def test_reset_password_request_invalid(self):
        with self.client:
            response = self.client.post(
                url_for('auth.reset_password_request_submit'),
                data=dict(email='j+resetfail@jlyons.me', submit='Request Reset'),
                follow_redirects=True
            )
            self.assertIn(b'There is no user associated with that email. Please try again.', response.data)

    def test_reset_password_valid(self):
        with self.client:
            user = User(email="j+change@jlyons.me")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

            token = user.get_reset_password_token()
            new_pass = 'newpassword'
            response = self.client.post(
                url_for('auth.reset_password_submit', token=token),
                data=dict(password=new_pass, password2=new_pass, submit='Reset Password'),
                follow_redirects=True
            )
            self.assertIn(b'Your password has been reset.', response.data)
            self.assertTrue(user.check_password(new_pass))

    """
    Helper Functions
    """
    def create_user(self):
        """Create test users."""
        self.user = User(name="Test User", email="j@jlyons.me")
        self.password = 'testing'
        self.user.set_password(self.password)

        db.session.add(self.user)
        db.session.commit()


if __name__ == "__main__":
    unittest.main()

"""Auth unit tests."""
import unittest
from app import app
from app.models import db, User


class AuthTests(unittest.TestCase):
    """Unit Tests"""

    def setUp(self):
        """Set up."""
        app.config.from_object("config.TestingConfig")

        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        """Tear down."""
        db.session.remove()
        db.drop_all()

    """Login"""
    def test_login(self):
        """Test root loads."""
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_valid_login(self):
        response = self.register('j+login@jlyons.me', 'testing', 'testing')
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.login('j+login@jlyons.me', 'testing')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in!', response.data)

    def test_login_invalid_login(self):
        response = self.register('j+login@jlyons.me', 'testing', 'testing')
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.login('j+login@jlyons.me', 'testings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)

    """Register"""
    def test_register(self):
        """Test root loads."""
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_register_valid_registration(self):
        response = self.register('j+succeed@jlyons.me', 'testing', 'testing')
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='j+succeed@jlyons.me').all()
        self.assertIsNotNone(user)

    def test_register_valid_confirm_email(self):
        email = 'j+confirm@jlyons.me'
        response = self.register(email, 'testing', 'testing')
        self.assertEqual(response.status_code, 200)

        user = User.query.filter_by(email=email).first()
        token = user.get_confirm_email_token()
        response = self.app.post(
            '/login?token={}'.format(token),
            follow_redirects=True
        )
        self.assertIn(b'Thank you. Your email has been confirmed!', response.data)
        self.assertTrue(user.email_confirmed)

    def test_register_invalid_confirm_email(self):
        email = 'j+confirm2@jlyons.me'
        response = self.register(email, 'testing', 'testing')
        self.assertEqual(response.status_code, 200)

        user = User.query.filter_by(email=email).first()
        response = self.app.post(
            '/login?token=fake-token',
            follow_redirects=True
        )
        self.assertIn(b'confirmation link is invalid.', response.data)
        self.assertFalse(user.email_confirmed)

    def test_register_invalid_duplicate_email(self):
        response = self.register('j+succeed@jlyons.me', 'testing', 'testing')
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.register('j+succeed@jlyons.me', 'testing', 'testing')
        self.assertIn(b'That email is already taken', response.data)

    def test_invalid_user_registration_passwords(self):
        response = self.register('j+fail@jlyons.me', 'testing', 'testings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords must match', response.data)
        user = User.query.filter_by(email='j+fail@jlyons.me').all()
        self.assertEqual(len(user), 0)

    """Reset Password Request"""
    def test_reset_password_request(self):
        """Test root loads."""
        response = self.app.get('/reset_password_request', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reset Password', response.data)

    def test_reset_password_request_valid(self):
        response = self.register('j+reset@jlyons.me', 'testing', 'testing')
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.app.post(
            '/reset_password_request',
            data=dict(email='j+reset@jlyons.me', submit='Request Reset'),
            follow_redirects=True
        )
        self.assertIn(b'Check your email for the instructions to reset your password', response.data)

    def test_reset_password_request_invalid(self):
        response = self.register('j+reset@jlyons.me', 'testing', 'testing')
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.app.post(
            '/reset_password_request',
            data=dict(email='j+reset2@jlyons.me', submit='Request Reset'),
            follow_redirects=True
        )
        self.assertIn(b'There is no user associated with that email. Please try again.', response.data)

    def test_reset_password_valid(self):
        email = 'j+reset2@jlyons.me'
        response = self.register(email, 'testing', 'testing')
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        user = User.query.filter_by(email=email).first()
        self.assertIsNotNone(user)

        self.assertTrue(user.check_password('testing'))
        token = user.get_reset_password_token()
        new_pass = 'newpassword'
        response = self.app.post(
            '/reset_password/{}'.format(token),
            data=dict(password=new_pass, password2=new_pass, submit='Reset Password'),
            follow_redirects=True
        )
        self.assertIn(b'Your password has been reset.', response.data)
        self.assertTrue(user.check_password(new_pass))

    """
    Helper Functions
    """

    def login(self, email, password, submit="Sign In"):
        """Login helper function."""
        return self.app.post(
            '/login',
            data=dict(email=email, password=password, submit=submit),
            follow_redirects=True
        )

    def register(self, email, password, password2, submit="Register"):
        """Register helper function."""
        return self.app.post(
            '/register',
            data=dict(email=email, password=password, password2=password2, submit=submit),
            follow_redirects=True
        )


if __name__ == "__main__":
    unittest.main()

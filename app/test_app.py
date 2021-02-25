"""App-wide unit tests."""
import unittest
from flask_testing import TestCase
from app import app
import app.tools as tools
from app.models import db, User, Merchant


class AppTests(TestCase):
    """Unit Tests"""
    headers = {}

    def create_app(self):
        app.config.from_object("config.TestingConfig")
        return app

    def setUp(self):
        """Set up."""
        self.tearDown()

        db.create_all()

        self.create_user()
        self.create_merchant()

    def tearDown(self):
        """Tear down."""
        db.session.remove()
        db.drop_all()

    def test_user_update_location(self):
        """user.update_location"""
        self.user.city = 'Omro'
        self.user.state = 'Wisconsin'
        db.session.commit()

        self.user.update_location(40.23, -111.6755)
        self.assertEqual(self.user.city, 'Provo')
        self.assertEqual(self.user.state, 'Utah')

    """
    Helper Functions
    """
    def create_user(self):
        """Create test users."""
        self.user = User(name="Test User", email="j@jlyons.me", phone="2084192692",
                         stripe_customer='cus_IsBcYPKgkKUnOa')
        self.password = 'testing'
        self.user.set_password(self.password)

        db.session.add(self.user)
        db.session.commit()

    def create_merchant(self):
        """Create test users."""
        self.merchant = Merchant()
        db.session.add(self.merchant)
        db.session.commit()


if __name__ == "__main__":
    unittest.main()

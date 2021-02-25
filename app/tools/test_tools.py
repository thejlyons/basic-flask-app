"""Tools unit tests."""
import unittest
from flask_testing import TestCase
from app import app
import app.tools as tools
from app.models import db, User, Merchant


class ToolsTests(TestCase):
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

    def test_phone_number_validator(self):
        """Test different test cases for test_phone_humber_validator"""
        test_cases = [
            {'phone': None, 'ret': None},
            {'phone': '', 'ret': None},
            {'phone': '2084192692', 'ret': '2084192692'},
            {'phone': '12084192692', 'ret': '2084192692'},
            {'phone': '+12084192692', 'ret': '2084192692'},
            {'phone': '(208) 419-2692', 'ret': '2084192692'},
            {'phone': '208)-419-2692', 'ret': '2084192692'},
            {'phone': '.,a\']=][\'ahs208asdcnjka=-]\';419.,.as;v[iuyhbnmas2692 , , ,, alsdkjhf', 'ret': '2084192692'},
            {'phone': '4192692', 'ret': None},
            {'phone': '2082084192692', 'ret': None},
            {'phone': '2084192692/0000000000', 'ret': '2084192692'},
            {'phone': '0000000000/2084192692', 'ret': '2084192692'},
            {'phone': 'tel:2084192692', 'ret': '2084192692'},
            {'phone': 'question:what is your number? answer:2084192692', 'ret': '2084192692'},
            {'phone': 'question:what is your number? answer:0000000000', 'ret': None},
            {'phone': '4089714455', 'ret': None}
        ]

        for case in test_cases:
            ret = tools.phone_number_validator(case['phone'])
            self.assertEqual(ret, case['ret'], f"Failed for {case}")

    def test_zip_code_data(self):
        """helper.zip_code_data"""
        lat, lng, _, _ = tools.zip_code_data(84601)
        self.assertEqual(lat, 40.2319)
        self.assertEqual(lng, -111.6755)

    def test_zip_code_dist(self):
        """helper.zip_code_dist"""
        dist = tools.zip_code_dist(84601, 84604)
        self.assertEqual(dist, 3.648599961105647)

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

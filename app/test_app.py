"""App-wide unit tests."""
import unittest
from app import app, db


class AppTests(unittest.TestCase):
    """Unit Tests"""

    def setUp(self):
        """Set up."""
        app.config.from_object("config.TestingConfig")

        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        """Tear down."""
        pass

    def test_index(self):
        """Test root loads."""
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()

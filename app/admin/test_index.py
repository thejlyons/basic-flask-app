"""Index unit tests."""
from flask_testing import TestCase
from flask import Flask, url_for
import os
from app import app, stripe
from app.models import db, User, Merchant, Redemption, Offer, PromoCode, Activity, Fundraiser, FundraiserCode, Region, \
    MagicLink, FoodtruckCheckIn
from unittest import mock
import unittest
import pendulum
from datetime import datetime
import json

basedir = os.path.abspath(os.path.dirname(__file__))


class IndexTests(TestCase):
    """Unit Tests"""

    def create_app(self):
        app.config.from_object("config.TestingConfig")
        return app

    def setUp(self):
        """Set up."""
        self.tearDown()

        db.create_all()

        self.create_user()
        self.create_merchant()
        self.create_fundraiser()

    def tearDown(self):
        """Tear down."""
        db.session.remove()
        db.drop_all()

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

    def create_fundraiser(self):
        """Create fundraiser."""
        self.fundraiser = Fundraiser(code='test', team_code='Test', active=True, owner_id=self.user.id)
        db.session.add(self.fundraiser)
        db.session.commit()


if __name__ == "__main__":
    unittest.main()

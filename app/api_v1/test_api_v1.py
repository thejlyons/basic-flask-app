"""Auth unit tests."""
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


class ApiV1Tests(TestCase):
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

    """Login"""
    # @mock.patch('app.tools.notify_text.delay')
    # def test_lead_new_no_phone(self, mock_notify_text):
    #     """Test api_v1.lead_new: check for non-existing lead."""
    #     with self.client:
    #         response = self.client.post(
    #             '/api/v1/lead/new',
    #             headers=self.headers,
    #             json={'id': 5},
    #             content_type='application/json',
    #             follow_redirects=True
    #         )
    #         self.assertEqual(response.status_code, 400)

    def test_push_token_valid(self):
        """api_v1.push_token: Test valid requests."""
        with self.client:
            cases = [
                {"id": self.user.id, "push_token": 'token1', "token": "token1"},
                {"id": self.user.id, "push_token": {"data": "token2", "type": "expo"}, "token": "token2"}
            ]

            for case in cases:
                response = self.client.post(
                    url_for('api_v1.push_token'),
                    json=case,
                    content_type='application/json',
                    follow_redirects=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(case['token'], self.user.expo_push_tokens, f"Token '{case['token']}' not added.")

    def test_push_token_invalid(self):
        """api_v1.push_token: Test invalid requests."""
        with self.client:
            cases = [
                {"id": self.user.id, "push_token": None, "token": None},
                {"id": None, "push_token": "invalid1", "token": "invalid1"},
                {"push_token": "invalid2", "token": "invalid2"},
                {"id": self.user.id, "push_token": {"data": None, "type": "expo"}, "token": None}
            ]

            for case in cases:
                response = self.client.post(
                    url_for('api_v1.push_token'),
                    json=case,
                    content_type='application/json',
                    follow_redirects=True
                )
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(case['token'], self.user.expo_push_tokens, f"Token '{case['token']}' was added.")

    def test_old_endpoints(self):
        """Test soon to be depricated endpoints for functionality."""
        with self.client:
            endpoints = [
                {'endpoint': '/grab-local-bulletins', 'response': []},
                {'endpoint': '/grab-uses', 'response': []},
                {'endpoint': '/grab-monthly-affiliate-sign-ups', 'response': 0},
                {'endpoint': '/grab-limited-uses', 'response': 0}
            ]
            for endpoint in endpoints:
                response = self.client.post(
                    f"/api/v1{endpoint['endpoint']}",
                    json=endpoint.get('body', {}),
                    content_type='application/json',
                    follow_redirects=True
                )
                self.assertEqual(response.status_code, 200)
                if endpoint.get('response') is not None:
                    data = json.loads(response.get_data(as_text=True))
                    self.assertEqual(data, endpoint['response'])

    def test_redeemed_today(self):
        """api_v1.redeemed_today: Test retrieve todays redemptions only."""
        with self.client:
            r1 = Redemption(user_id=self.user.id, merchant_id=self.merchant.id, created=pendulum.now('UTC')
                            .subtract(days=1))
            r2 = Redemption(user_id=self.user.id, merchant_id=self.merchant.id, created=pendulum.now('UTC'))
            db.session.add(r1)
            db.session.add(r2)

            response = self.client.post(
                url_for('api_v1.redeemed_today'),
                json={'user': self.user.as_dict(), 'merchant': self.merchant.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['id'], r2.id)

    def test_redeemed_today_empty(self):
        """api_v1.redeemed_today: Test retrieve todays redemptions only."""
        with self.client:
            r1 = Redemption(user_id=self.user.id, merchant_id=self.merchant.id, created=pendulum.now().subtract(days=1))
            db.session.add(r1)

            response = self.client.post(
                url_for('api_v1.redeemed_today'),
                json={'user': self.user.as_dict(), 'merchant': self.merchant.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(len(data), 0)

    @mock.patch('app.tools.send_twilio_sms')
    def test_redeem(self, mock_send_twilio_sms):
        """api_v1.redeem: Test redeem offer."""
        with self.client:
            offer = Offer(merchant_id=self.merchant.id, offer="Special", value=10, deal_limit=20)
            db.session.add(offer)
            db.session.commit()

            response = self.client.post(
                '/api/v1/redeem',
                json={'user': self.user.as_dict(), 'restaurant': self.merchant.as_dict(), 'time': 11,
                      'value': offer.value, 'day': 'Sunday', 'offer': offer.as_dict(), 'check_in_type': 'happyHour'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            r = Redemption.query.filter_by(user_id=self.user.id, merchant_id=self.merchant.id).first()
            self.assertIsNotNone(r)
            self.assertNotIn(offer.id, self.user.redeemed_offers)
            self.assertEqual(r.check_in_type, 'happyHour')

    def test_redeem_alternate_endpoints(self):
        """api_v1.redeem: Test /use-button."""
        with self.client:
            cases = [
                {'check_in_type': 'happyHour', 'endpoint': '/use-button', 'in_redeemed_offers': False},
                {'check_in_type': 'allDay', 'endpoint': '/use-all-day', 'in_redeemed_offers': False},
                {'check_in_type': 'foodtruck', 'endpoint': '/use-foodtruck', 'in_redeemed_offers': False},
                {'check_in_type': 'specialOffer', 'endpoint': '/use-special-offer', 'in_redeemed_offers': True},
            ]
            for case in cases:
                offer = Offer(merchant_id=self.merchant.id, offer="Special", value=10, deal_limit=20)
                db.session.add(offer)
                db.session.commit()

                response = self.client.post(
                    f"/api/v1{case['endpoint']}",
                    json={'user': self.user.as_dict(), 'restaurant': self.merchant.as_dict(), 'time': 11,
                          'value': offer.value, 'day': 'Sunday', 'offer': offer.as_dict()},
                    content_type='application/json',
                    follow_redirects=True
                )
                self.assertEqual(response.status_code, 200)
                r = Redemption.query.filter_by(user_id=self.user.id, merchant_id=self.merchant.id)\
                    .order_by(Redemption.id.desc()).first()
                self.assertIsNotNone(r)
                if case['in_redeemed_offers']:
                    self.assertIn(offer.id, self.user.redeemed_offers)
                else:
                    self.assertNotIn(offer.id, self.user.redeemed_offers)
                self.assertEqual(r.check_in_type, case['check_in_type'])

    def test_redemption_get(self):
        """api_v1.redemption_get: Test get all redemptions."""
        with self.client:
            r1 = Redemption(user_id=self.user.id, merchant_id=self.merchant.id, created=pendulum.now('UTC')
                            .subtract(days=1))
            r2 = Redemption(user_id=self.user.id, merchant_id=self.merchant.id, created=pendulum.now('UTC'))
            db.session.add(r1)
            db.session.add(r2)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.redemption_get'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(len(data), 2)
            self.assertEqual(r1.id, data[0]['id'])
            self.assertEqual(r2.id, data[1]['id'])

    def test_user_get(self):
        """api_v1.user_get: Test get user."""
        with self.client:
            promo = PromoCode(team_code="Pass360 Test")
            db.session.add(promo)
            db.session.commit()
            self.user.promo_id = promo.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.user_get'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['team_code'], promo.team_code)
            self.assertEqual(data['success'], True)
            self.assertEqual(data['id'], self.user.id)

    def test_deactivate_iap(self):
        """api_v1.deactivate_iap: Test deactivate in-app purchase."""
        with self.client:
            promo = PromoCode(team_code="Pass360 Test")
            db.session.add(promo)
            db.session.commit()

            self.user.active = True
            self.user.promo_id = promo.id
            self.user.promo_timestamp = datetime.now()
            response = self.client.post(
                url_for('api_v1.deactivate_iap'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            self.assertFalse(self.user.active)
            self.assertIsNone(self.user.promo_id)
            self.assertIsNone(self.user.promo_timestamp)

            act = Activity.query.filter_by(user_id=self.user.id).first()
            self.assertIsNotNone(act)
            self.assertEqual(act.action, 'Cancellation')
            self.assertTrue(act.apple)

    @mock.patch('app.tools.send_twilio_sms')
    def test_webhook_prepaid(self, mock_send_twilio_sms=None):
        """api_v1.webhook_prepaid: Test stripe purchase webhook."""
        with self.client:
            promo_code = PromoCode.create_fundraiser_code(self.fundraiser.id)

            fc = FundraiserCode(user_id=self.user.id, promo_code_id=promo_code.id, fundraiser_id=self.fundraiser.id,
                                phone=self.user.phone, name=self.user.name, quantity=1)
            db.session.add(fc)
            db.session.commit()

            payload = {
                "id": "evt_1IGAQkGEmq6oGaZngpssP33i",
                "object": "event",
                "api_version": "2018-02-28",
                "created": 1612216774,
                "data": {
                    "object": {
                        "id": "cs_test_a158typjkbEvcRUdsvnPRQIcZO7d7I3fjpAJGEorHv4fz4qBIN9fVJNyuc",
                        "object": "checkout.session",
                        "allow_promotion_codes": None,
                        "amount_subtotal": 2500,
                        "amount_total": 2500,
                        "billing_address_collection": None,
                        "cancel_url": "https://www.passthreesixty.com/fundraising/hNjtSbqk",
                        "client_reference_id": f"{promo_code.barcode}|1",
                        "currency": "usd",
                        "customer": "cus_IruF7q6UGKzaJp",
                        "customer_details": {
                            "email": "lyons.josh@yahoo.com",
                            "tax_exempt": "none",
                            "tax_ids": []
                        },
                        "customer_email": None,
                        "livemode": False,
                        "locale": None,
                        "metadata": {},
                        "mode": "payment",
                        "payment_intent": "pi_1IGAQIGEmq6oGaZn0BFPfVVL",
                        "payment_method_types": [
                            "card"
                        ],
                        "payment_status": "paid",
                        "setup_intent": None,
                        "shipping": None,
                        "shipping_address_collection": None,
                        "submit_type": None,
                        "subscription": None,
                        "success_url": "https://www.passthreesixty.com/redeemed/hNjtSbqk",
                        "total_details": {
                            "amount_discount": 0,
                            "amount_tax": 0
                        }
                    }
                },
                "livemode": False,
                "pending_webhooks": 3,
                "request": {
                    "id": None,
                    "idempotency_key": None
                },
                "type": "checkout.session.completed"
            }
            response = self.client.post(
                url_for('api_v1.webhook_prepaid'),
                json=payload,
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            m = f"Congratulations your payment has been processed! To redeem your 1-year pass go to the " \
                f"Pass 360 app and enter your single-use access code: {promo_code.code}"
            mock_send_twilio_sms.assert_called_with(m, self.user.phone, f"+1{os.environ['TWILIO_PHONE']}")

    @mock.patch('app.tools.send_twilio_sms')
    def test_webhook_prepaid_multiple(self, mock_send_twilio_sms=None):
        """api_v1.webhook_prepaid: Test stripe purchase webhook for multiple codes."""
        with self.client:
            promo_code = PromoCode.create_fundraiser_code(self.fundraiser.id)

            fc = FundraiserCode(user_id=self.user.id, promo_code_id=promo_code.id, fundraiser_id=self.fundraiser.id,
                                phone=self.user.phone, name=self.user.name, quantity=1)
            db.session.add(fc)
            db.session.commit()

            payload = {
                "id": "evt_1IGAQkGEmq6oGaZngpssP33i",
                "object": "event",
                "api_version": "2018-02-28",
                "created": 1612216774,
                "data": {
                    "object": {
                        "id": "cs_test_a158typjkbEvcRUdsvnPRQIcZO7d7I3fjpAJGEorHv4fz4qBIN9fVJNyuc",
                        "object": "checkout.session",
                        "allow_promotion_codes": None,
                        "amount_subtotal": 2500,
                        "amount_total": 2500,
                        "billing_address_collection": None,
                        "cancel_url": "https://www.passthreesixty.com/fundraising/hNjtSbqk",
                        "client_reference_id": f"{promo_code.barcode}|3",
                        "currency": "usd",
                        "customer": "cus_IruF7q6UGKzaJp",
                        "customer_details": {
                            "email": "lyons.josh@yahoo.com",
                            "tax_exempt": "none",
                            "tax_ids": []
                        },
                        "customer_email": None,
                        "livemode": False,
                        "locale": None,
                        "metadata": {},
                        "mode": "payment",
                        "payment_intent": "pi_1IGAQIGEmq6oGaZn0BFPfVVL",
                        "payment_method_types": [
                            "card"
                        ],
                        "payment_status": "paid",
                        "setup_intent": None,
                        "shipping": None,
                        "shipping_address_collection": None,
                        "submit_type": None,
                        "subscription": None,
                        "success_url": "https://www.passthreesixty.com/redeemed/hNjtSbqk",
                        "total_details": {
                            "amount_discount": 0,
                            "amount_tax": 0
                        }
                    }
                },
                "livemode": False,
                "pending_webhooks": 3,
                "request": {
                    "id": None,
                    "idempotency_key": None
                },
                "type": "checkout.session.completed"
            }
            response = self.client.post(
                url_for('api_v1.webhook_prepaid'),
                json=payload,
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(fc.quantity, 3)
            self.assertEqual(len(fc.all_codes), 3)
            new_line = '\n'
            m = f"Congratulations your payment has been processed! To redeem your 1-year pass go to " \
                f"the Pass 360 app and enter your single-use access codes:\n{new_line.join(fc.all_codes)}"
            mock_send_twilio_sms.assert_called_with(m, self.user.phone, f"+1{os.environ['TWILIO_PHONE']}")

    def test_cancel_subscription(self):
        """api_v1.cancel_subscription: Test cancel subscription for Stripe users."""
        with self.client:
            subscription = stripe.Subscription.create(
                customer=self.user.stripe_customer,
                items=[
                    {"price": app.config['STRIPE_SUBSCRIPTION_ID']},
                ],
            )
            self.user.active = True
            self.user.stripe_subscription = subscription.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.cancel_subscription'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.user = User.get(self.user.id)

            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.user.active)

            subscription = stripe.Subscription.retrieve(self.user.stripe_subscription)
            self.assertEqual(subscription['status'], 'canceled')

    def test_update_card(self):
        """api_v1.update_card: Test update subscription payment method."""
        with self.client:
            subscription = stripe.Subscription.create(
                customer=self.user.stripe_customer,
                items=[
                    {"price": app.config['STRIPE_SUBSCRIPTION_ID']},
                ],
            )
            self.user.active = True
            self.user.stripe_subscription = subscription.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.update_card'),
                json={'user': self.user.as_dict(), 'token': 'tok_mastercard'},
                content_type='application/json',
                follow_redirects=True
            )
            self.user = User.get(self.user.id)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.user.active)
            stripe.Subscription.delete(self.user.stripe_subscription)
            customer = stripe.Customer.retrieve(self.user.stripe_customer)
            card = customer.get('sources', {}).get('data', [None])[1]
            stripe.Customer.delete_source(self.user.stripe_customer, card['id'])

    def test_activate_account(self):
        """api_v1.activate_account: Test update subscription payment method."""
        with self.client:
            user = User(name="Test User", email="j+activateaccount@jlyons.me", phone="2084192692", active=False)
            user.set_password('testing')

            db.session.add(user)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.activate_account'),
                json={'user': user.as_dict(), 'token': 'tok_mastercard'},
                content_type='application/json',
                follow_redirects=True
            )

            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(user.stripe_customer)
            self.assertIsNotNone(user.stripe_subscription)
            self.assertTrue(user.active)
            stripe.Subscription.delete(user.stripe_subscription)
            stripe.Customer.delete(user.stripe_customer)

    def test_iap_activation(self):
        """api_v1.iap_activation: Test update subscription payment method."""
        with self.client:
            self.user.active = False
            self.user.iap_receipt = None
            db.session.commit()

            receipt = 'asdf'
            response = self.client.post(
                url_for('api_v1.iap_activation'),
                json={'user': self.user.as_dict(), 'receipt': receipt},
                content_type='application/json',
                follow_redirects=True
            )
            self.user = User.get(self.user.id)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.user.active)
            self.assertEqual(self.user.iap_receipt, receipt)

    def test_handle_promo(self):
        """api_v1.handle_promo: Test handle promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=True, prepaid=True, redeemed=False)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.handle_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.user.active)
            self.assertEqual(self.user.promo_id, promo.id)
            self.assertIsNotNone(self.user.promo_timestamp)

    def test_handle_promo_redeemed(self):
        """api_v1.handle_promo: Test handle promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=True, prepaid=False, redeemed=True)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.handle_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code},
                content_type='application/json',
                follow_redirects=True
            )
            data = json.loads(response.get_data(as_text=True))
            self.assertIn('error', data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.user.active)

    def test_handle_promo_redeemed_prepaid(self):
        """api_v1.handle_promo: Test handle promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=True, prepaid=True, redeemed=True)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.handle_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code},
                content_type='application/json',
                follow_redirects=True
            )
            data = json.loads(response.get_data(as_text=True))
            self.assertIn('error', data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.user.active)
            self.assertIsNone(self.user.promo_id)
            self.assertIsNone(self.user.promo_timestamp)

    def test_handle_promo_not_prepaid(self):
        """api_v1.handle_promo: Test handle promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=False, prepaid=False, redeemed=True)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.handle_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code},
                content_type='application/json',
                follow_redirects=True
            )
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['must_pay'])
            self.assertFalse(self.user.active)
            self.assertIsNone(self.user.promo_id)
            self.assertIsNone(self.user.promo_timestamp)

    def test_activate_promo(self):
        """api_v1.activate_promo: Test activate promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=True, prepaid=False, redeemed=False)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.activate_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code, 'receipt': 'asdf'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.user.active)
            self.assertEqual(self.user.promo_id, promo.id)
            self.assertIsNotNone(self.user.promo_timestamp)
            self.assertEqual(self.user.iap_receipt, 'asdf')

    def test_activate_promo_already_redeemed(self):
        """api_v1.activate_promo: Test activate promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=True, prepaid=False, redeemed=True)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.activate_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code},
                content_type='application/json',
                follow_redirects=True
            )
            data = json.loads(response.get_data(as_text=True))
            self.assertIn('error', data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.user.active)
            self.assertIsNone(self.user.promo_id)
            self.assertIsNone(self.user.promo_timestamp)

    def test_activate_promo_multi_use(self):
        """api_v1.activate_promo: Test activate promo endpoint."""
        with self.client:
            self.user.active = False
            self.user.promo_id = None
            self.user.promo_timestamp = None
            promo = PromoCode(code='asdf', single_use=False, prepaid=False, redeemed=True)
            db.session.add(promo)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.activate_promo'),
                json={'user': self.user.as_dict(), 'code': promo.code, 'token': 'tok_amex'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.user.active)
            self.assertEqual(self.user.promo_id, promo.id)
            self.assertIsNotNone(self.user.promo_timestamp)

    def test_get_card_details(self):
        """api_v1.get_card_details: Test get card details endpoint."""
        with self.client:
            response = self.client.post(
                url_for('api_v1.get_card_details'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['card']['last4'], '4242')

    @mock.patch('app.tools.google_api_location')
    def test_grab_regions(self, mock_google_api_location):
        """api_v1.grab_regions: Test get card details endpoint."""
        with self.client:
            lat = 40.2128559
            lng = -111.7256936
            mock_google_api_location.return_value = [lat, lng]
            region = Region()
            db.session.add(region)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.grab_regions'),
                json={'zip': '84601'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))

            self.assertEqual(data['regions'][0]['id'], region.id)
            self.assertEqual(data['latitude'], lat)
            self.assertEqual(data['longitude'], lng)
            mock_google_api_location.assert_called_with('84601')

    def test_fundraising_clear(self):
        """api_v1.fundraising_clear: Clear fundraising."""
        with self.client:
            self.user.fundraiser_id = self.fundraiser.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.fundraising_clear'),
                json={'user_id': self.user.id},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(self.user.fundraiser_id)

    def test_fundraising_get(self):
        """api_v1.fundraising_get: Clear fundraising."""
        with self.client:
            self.user.fundraiser_id = self.fundraiser.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.fundraising_get'),
                json={'user_id': self.user.id},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            # TODO: Make sure the correct codes are retrieved

    def test_fundraising_set(self):
        """api_v1.fundraising_set: Set fundraising."""
        with self.client:
            self.user.fundraiser_id = None
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.fundraising_set'),
                json={'user_id': self.user.id, 'name': self.user.name, 'code': self.fundraiser.code},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.user.fundraiser_id, self.fundraiser.id)

            data = json.loads(response.get_data(as_text=True))
            self.assertNotEqual(data, {})
            self.assertTrue(data['fundraising'])
            self.assertEqual(data['fundraiser']['id'], self.fundraiser.id)

    def test_fundraising_set_wrong(self):
        """api_v1.fundraising_set: Try to set an invalid fundraiser."""
        with self.client:
            self.user.fundraiser_id = None
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.fundraising_set'),
                json={'user_id': self.user.id, 'name': self.user.name, 'code': 'wrong'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(self.user.fundraiser_id)

            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data, {})

    @mock.patch('app.tools.send_twilio_sms')
    def test_fundraising_invite(self, mock_send_twilio_sms):
        """api_v1.fundraising_invite: Send fundraiser invitation."""
        with self.client:
            self.user.fundraiser_id = self.fundraiser.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.fundraising_invite'),
                json={'user_id': self.user.id, 'name': 'Invite Name', 'phone': '2084192692'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            new_link = FundraiserCode.query.filter_by(user_id=self.user.id).order_by(FundraiserCode.id.desc()).first()
            new_code = PromoCode.query.get(new_link.promo_code_id)
            body = Fundraiser.invite_message(self.user.name, new_code.barcode, None)
            mock_send_twilio_sms.assert_called_with(body, '2084192692')

    @mock.patch('app.tools.send_twilio_sms')
    def test_fundraising_invite_resend(self, mock_send_twilio_sms):
        """api_v1.fundraising_invite_resend: Re-send fundraiser invitation."""
        with self.client:
            self.user.fundraiser_id = self.fundraiser.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.fundraising_invite'),
                json={'user_id': self.user.id, 'name': 'Invite Resend', 'phone': '2084192692'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            response = self.client.post(
                url_for('api_v1.fundraising_invite_resend'),
                json={'user_id': self.user.id, 'name': 'Invite Resend', 'phone': '2084192692'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            links = FundraiserCode.query.filter_by(user_id=self.user.id, phone='2084192692', name='Invite Resend',
                                                   fundraiser_id=self.fundraiser.id).all()
            self.assertEqual(len(links), 1)

            new_link = FundraiserCode.query.filter_by(user_id=self.user.id).order_by(FundraiserCode.id.desc()).first()
            new_code = PromoCode.query.get(new_link.promo_code_id)
            body = Fundraiser.invite_message(self.user.name, new_code.barcode, None)
            mock_send_twilio_sms.assert_called_with(body, '2084192692')

    def test_merchant(self):
        """api_v1.merchant: Get single merchant by id."""
        with self.client:
            response = self.client.post(
                url_for('api_v1.merchant', merchant_id=self.merchant.id),
                json={},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

    def test_four_digit_login(self):
        """api_v1.four_digit_login: Login with a four-digit code."""
        with self.client:
            code = MagicLink(phone=self.user.phone, user_id=self.user.id)
            code.set_code()
            db.session.add(code)
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.four_digit_login'),
                json={'phone': self.user.phone, 'four_digit': code.code},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['id'], self.user.id)

    @mock.patch('app.tools.send_twilio_sms')
    def test_authenticate(self, mock_send_twilio_sms):
        """api_v1.authenticate: Authenticate user."""
        with self.client:
            response = self.client.post(
                url_for('api_v1.register_phone'),
                json={'phone': self.user.phone},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['phone'], self.user.phone)

            ml = MagicLink.query.filter_by(phone=data['phone']).order_by(MagicLink.id.desc()).first()
            mock_send_twilio_sms.assert_called_with(ml.get_message(), self.user.phone)

            response = self.client.post(
                url_for('api_v1.four_digit_login'),
                json={'phone': self.user.phone, 'four_digit': ml.code},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['id'], self.user.id)

    @mock.patch('app.tools.send_twilio_sms')
    def test_register_phone(self, mock_send_twilio_sms):
        """api_v1.register_phone: Register phone and generate 4-digit code."""
        with self.client:
            response = self.client.post(
                url_for('api_v1.register_phone'),
                json={'phone': self.user.phone},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['phone'], self.user.phone)
            ml = MagicLink.query.filter_by(phone=data['phone']).order_by(MagicLink.id.desc()).first()
            mock_send_twilio_sms.assert_called_with(ml.get_message(), self.user.phone)

    @mock.patch('app.tools.send_twilio_sms')
    def test_register_phone_new(self, mock_send_twilio_sms):
        """api_v1.register_phone: Register phone and generate 4-digit code."""
        with self.client:
            response = self.client.post(
                url_for('api_v1.register_phone'),
                json={'phone': '8019199190'},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['phone'], '8019199190')
            ml = MagicLink.query.filter_by(phone='8019199190').order_by(MagicLink.id.desc()).first()
            mock_send_twilio_sms.assert_called_with(ml.get_message(), '8019199190')

    def test_category_list(self):
        """api_v1.category_list: Get all categories and sub-categories."""
        with self.client:
            # TODO: test this
            response = self.client.post(
                url_for('api_v1.category_list'),
                json={},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            # self.assertEqual(False, True)

    def test_foodtruck(self):
        """api_v1.foodtruck: Get user's foodtruck."""
        with self.client:
            self.user.foodtruck_id = self.merchant.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.foodtruck'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertEqual(data['id'], self.merchant.id)

    def test_foodtruck_none(self):
        """api_v1.foodtruck: Test error returned if no foodtruck found."""
        with self.client:
            self.user.foodtruck_id = None
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.foodtruck'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertIn('error', data)

    def test_foodtruck_action(self):
        """api_v1.foodtruck: Test error returned if no foodtruck found."""
        with self.client:
            self.user.foodtruck_id = self.merchant.id
            db.session.commit()

            response = self.client.post(
                url_for('api_v1.foodtruck_action', action='start'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.get_data(as_text=True))
            self.assertNotIn('error', data)

            ci = FoodtruckCheckIn.query.filter_by(foodtruck_id=self.merchant.id, end=None)\
                .order_by(FoodtruckCheckIn.id.desc()).first()

            self.assertIsNotNone(ci)
            self.assertIsNotNone(ci.start)

            response = self.client.post(
                url_for('api_v1.foodtruck_action', action='end'),
                json={'user': self.user.as_dict()},
                content_type='application/json',
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

            self.assertIsNotNone(ci)
            self.assertIsNotNone(ci.end)

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

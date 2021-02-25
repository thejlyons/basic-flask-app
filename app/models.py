"""Models."""
from flask import url_for, flash
from flask_login import UserMixin, current_user
from app import app, db, login, stripe, geolocator
from app.tools import send_twilio_sms, phone_number_validator, generate_code
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm.attributes import flag_modified
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from time import time
import os
from sqlalchemy import text
from datetime import datetime
import pendulum


@login.user_loader
def load_user(user_id):
    """Retrieve individual on login success."""
    individual = None
    if user_id:
        individual = User.query.get(int(user_id))
    return individual


class User(UserMixin, db.Model):
    """
    User.

    Object for each account.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String(120), unique=True)
    email_confirmed = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    active = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    password_hash = db.Column(db.String(128))

    # Location data
    zip_code = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    max_distance = db.Column(db.Integer, default=25, server_default='25')
    stripe_customer = db.Column(db.String())
    stripe_subscription = db.Column(db.String())
    iap_receipt = db.Column(db.String())
    redeemed_offers = db.Column(db.JSON(), default=[], server_default='[]')
    expo_push_tokens = db.Column(db.JSON(), default=[], server_default='[]')
    admin = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    edit = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    promo_id = db.Column(db.Integer, db.ForeignKey('promo_code.id', ondelete='SET NULL'))
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraiser.id', ondelete='SET NULL'))
    foodtruck_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='SET NULL'))
    promo_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get(id=None, email=None, phone=None):
        """Get User by given parameters."""
        if id:
            return User.query.get(id)
        elif email:
            return User.get_by_email(email.lower())
        elif phone:
            return User.get_by_phone(phone)

    @staticmethod
    def get_by_phone(phone):
        """Get User by email."""
        return User.query.filter_by(phone=phone).first()

    @staticmethod
    def get_by_email(email):
        """Get User by email."""
        return User.query.filter_by(email=email).first()

    def get_name(self):
        """Get name."""
        return self.email

    def set_password(self, password):
        """Set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password."""
        return check_password_hash(self.password_hash, password)

    def get_landing_page(self):
        return url_for('admin.merchants')

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

    @validates('email')
    def validate_email(self, key, value):
        """Validate Email."""
        return value.lower()

    @validates('phone')
    def validate_phone(self, key, value):
        """Validate Phone."""
        phone = phone_number_validator(value)
        assert phone is not None
        return value

    @staticmethod
    def admin_list_all(offset, limit, search):
        """Get list of all users"""
        query = "select {0} from \"user\"{1}{2}".format

        body = "id, name, phone, email, active, city, state, stripe_customer, stripe_subscription, promo_id, (select" \
               " code from promo_code where promo_code.id = promo_id) as promo, (SELECT json_agg(json_build_object(" \
               "'id', id, 'note', note, 'created', created) ORDER BY user_note.id DESC) FROM user_note WHERE " \
               "user_note.user_id = \"user\".id) as notes"

        if search:
            search = f" where (name ~* '{search}' or phone ~* '{search}' or email ~* '{search}' or city ~* '{search}'" \
                     f" or state ~* '{search}')"

        total = f" order by id desc limit {limit} offset {offset * limit}"
        sql = text(query(body, search, total))
        results = db.engine.execute(sql)

        users = []
        for u in results:
            users.append(User.admin_dict_from_row(u))

        sql = text(query('count(*)', search, ''))
        result = db.engine.execute(sql)
        count = 0
        for row in result:
            count = row[0]

        return users, count

    @staticmethod
    def admin_dict_from_row(u):
        """Dict from row."""
        return {
            'id': u[0],
            'name': u[1],
            'phone': u[2],
            'email': u[3],
            'active': u[4],
            'city': u[5],
            'state': u[6],
            'stripe_customer': u[7],
            'stripe_subscription': u[8],
            'promo_id': u[9],
            'promo': u[10],
            'notes': u[11]
        }

    def activate_promo(self, code_id):
        """Record promo code activation and activate account."""
        self.active = True
        self.promo_id = code_id
        self.promo_timestamp = datetime.utcnow()
        db.session.commit()

    def create_stripe_customer(self, token):
        """Create customer object in stripe."""
        if self.stripe_customer is None:
            customer = stripe.Customer.create(
                source=token,
                description=f"Customer for {self.phone if self.phone is not None else self.email}",
            )
            self.stripe_customer = customer['id']
            db.session.commit()
        return self.stripe_customer

    def create_stripe_subscription(self):
        """Create customer object in stripe."""
        subscription = stripe.Subscription.create(
            customer=self.stripe_customer,
            items=[
                {"price": app.config['STRIPE_SUBSCRIPTION_ID']},
            ],
        )
        self.stripe_subscription = subscription['id']
        self.active = True

        Activity.activate(self.id, 399)

        return self.stripe_subscription

    def update_card(self, token):
        """Update subscription payment method to card from given token."""
        if self.stripe_subscription is not None and token is not None:
            card = stripe.Customer.create_source(self.stripe_customer, source=token)
            if card is not None:
                stripe.Subscription.modify(self.stripe_subscription, default_payment_method=card['id'])
                self.active = True
                db.session.commit()

    def update_location(self, lat, lng):
        """Update location of user and store in DB."""
        if lat is not None and lng is not None:
            self.latitude = lat
            self.longitude = lng

            location = geolocator.reverse(f"{lat}, {lng}")
            if location:
                city = location.raw.get('address', {}).get('city')
                if city is not None:
                    self.city = city
                state = location.raw.get('address', {}).get('state')
                if state is not None:
                    self.state = state
            db.session.commit()

    def __str__(self):
        """Return str representation of model."""
        return f"{self.email} ({self.id})"

    def as_dict(self):
        """Dict repr."""
        # TODO: update all as_dict methods
        return {
            'id': self.id,
            'name': self.name,
            'active': self.active,
            'phone': self.phone,
            'email': self.email,
            'email_confirmed': self.email_confirmed,
            'password_hash': self.password_hash,
            'redeemed_offers': self.redeemed_offers,
            'expo_push_tokens': self.expo_push_tokens,
            'admin': self.admin,
            'zip': self.zip_code,
            'zip_code': self.zip_code,
            'edit': self.edit,
            'promo_id': self.promo_id,
            'promo_timestamp': self.promo_timestamp,
            'promo': self.promo_timestamp.timestamp() * 1000 if self.promo_timestamp else None,
            'created': self.created,
        }


class Merchant(db.Model):
    """
    Merchant.

    Object for each merchant.
    """
    default_limit = 10
    default_max = 175

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    name = db.Column(db.String())
    images = db.Column(db.JSON())
    approved = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    coming_soon = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    deleted = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    # Internal checklist
    terms_agreed = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    welcome_email = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    go_live_text = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    instagram = db.Column(db.String())
    facebook = db.Column(db.String())
    website = db.Column(db.String())

    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def new():
        """Create a new merchant."""
        merchant = Merchant(user_id=current_user.id)
        db.session.add(merchant)
        db.session.commit()

        return merchant

    @staticmethod
    def delete(data):
        """Delete merchant."""
        if data is not None and data.get('id') is not None:
            merchant = Merchant.query.get(data['id'])
            merchant.deleted = True
            db.session.commit()

    @staticmethod
    def save(data):
        """Create a new merchant."""
        if data is not None:
            merchant = Merchant.query.get(data['id'])
            if merchant:
                merchant.name = data.get('name', None)
                merchant.images = data.get('images', [])
                merchant.approved = data.get('approved', False)
                merchant.coming_soon = data.get('coming_soon', False)

                merchant.instagram = data.get('instagram')
                merchant.facebook = data.get('facebook')
                merchant.website = data.get('website')
                flag_modified(merchant, 'images')
                db.session.commit()

    @staticmethod
    def admin_list_all(offset, limit, search):
        query = "select {0} from merchant where deleted = 'f'{1}{2}".format
        """Get list of all merchants"""

        body = "id, user_id, approved, coming_soon, instagram, website, created, (select count(*) from location where" \
               " merchant_id = merchant.id) as num_locations, facebook, name, (SELECT json_agg(json_build_object(" \
               "'id', id, 'note', note, 'created', created) ORDER BY merchant_note.id DESC) FROM merchant_note WHERE " \
               "merchant_note.merchant_id = merchant.id) as notes, images, (SELECT json_agg(json_build_object('id'," \
               " id, 'merchant_id', merchant_id, 'hours', hours, 'offer', offer, 'details', details, 'code', code, " \
               "'code_link', code_link, 'deal_limit', deal_limit, 'value', value, 'is_bogo', is_bogo, 'single_use', " \
               "single_use, 'happy_hour', happy_hour, 'redemptions', (select count(*) from redemption where " \
               "redemption.offer_id = offer.id)) ORDER BY offer.id DESC) FROM offer WHERE offer.merchant_id = " \
               "merchant.id) as offers, (SELECT json_agg(json_build_object('id', id, 'merchant_id', merchant_id, " \
               "'place_id', place_id, 'lat', lat, 'lng', lng, 'address', address, 'address2', address2, 'city', city," \
               " 'state', state, 'zip_code', zip_code, 'phone', phone, 'created', created, 'notes', (SELECT " \
               "json_agg(json_build_object('id', id, 'note', note, 'created', created) ORDER BY location_note.id " \
               "DESC) FROM location_note WHERE location_note.location_id = location.id)) ORDER BY location.id DESC) " \
               "FROM location WHERE location.merchant_id = merchant.id) as locations, (SELECT " \
               "json_agg(json_build_object('id', id, 'merchant_id', merchant_id, 'name', name, 'phone', phone)"\
               " ORDER BY merchant_contact.id DESC) FROM merchant_contact WHERE merchant_contact.merchant_id = " \
               "merchant.id) as contacts"

        if search:
            search = f" and (name ~* '{search}')"

        limit = int(limit)
        offset = int(offset)
        total = f" order by id desc limit {limit} offset {offset * limit}"
        sql = text(query(body, search, total))
        results = db.engine.execute(sql)

        merchants = []
        for m in results:
            merchants.append(Merchant.admin_dict_from_row(m))

        sql = text(query('count(*)', search, ''))
        result = db.engine.execute(sql)
        count = 0
        for row in result:
            count = row[0]

        return merchants, count

    @staticmethod
    def list_all(offset, max_distance, lat, lng, alpha=False):
        """Get list of all merchants"""
        if lat is None:
            lat = 40.2518435
        if lng is None:
            lng = -111.6493156

        dist_calc = f", 2 * 3961 * asin(sqrt((sin(radians((latitude - {lat}) / 2))) ^ 2 + cos(radians({lat})) " \
                    f"*cos(radians(latitude)) * (sin(radians((longitude - {lng}) / 2))) ^ 2)) as distance;"

        limit = Merchant.default_max if offset is None else Merchant.default_limit
        offset = 0 if offset is None else Merchant.default_limit * int(offset)

        order_by = f'ORDER BY distance, name, id NULLS FIRST LIMIT {limit} OFFSET {offset}'
        if alpha:
            order_by = f'ORDER BY name'

        offer_query = "(SELECT json_agg(json_build_object('id', id, 'offer', offer, 'value', value, 'details', " \
                      "details, 'code', code, 'code_link', code_link, 'is_bogo', is_bogo, 'hours', hours)) FROM " \
                      "offer WHERE merchant_id=merchant.id and {0}) AS {1},".format
        special_offers = offer_query("offer.single_use = 't'", 'special_offers')
        ongoing_offers = offer_query("offer.single_user = 'f' and offer.happy_hour = 'f'", 'special_offers')
        happy_hours = offer_query("offer.happy_hour = 't'", 'special_offers')

        # TODO: re-add support for seasonal merchants
        # seasonal_open = "and (seasonal_open is null or (date_part('month', seasonal_open) < date_part('month', " \
        #                 "now()) or (date_part('month', seasonal_open) = date_part('month', now()) and " \
        #                 "date_part('day', seasonal_open) <= date_part('day', now()))))"
        # seasonal_close = "and (seasonal_close is null or (date_part('month', seasonal_close) > date_part('month', " \
        #                  "now()) or (date_part('month', seasonal_close) = date_part('month', now()) and " \
        #                  "date_part('day', seasonal_close) >= date_part('day', now()))))"

        sql = text(f"WITH merchant_distance as (SELECT *{dist_calc}, {special_offers} {ongoing_offers} {happy_hours} "
                   f"from merchants where approved = 't' or coming_soon = 't') select merchant_distance.* from "
                   f"merchant_distance where (distance <= {max_distance} or online = 't') {order_by}")
        results = db.engine.execute(sql)

        merchants = []
        for m in results:
            merchants.append(Merchant.dict_from_row(m))
        return merchants

    @staticmethod
    def dict_from_row(m):
        """Build dict from given row"""
        print(m)
        return {}

    @staticmethod
    def admin_dict_from_row(m):
        """Build dict from given row"""
        return {
            'id': m[0],
            'user_id': m[1],
            'approved': m[2],
            'coming_soon': m[3],
            'instagram': m[4],
            'website': m[5],
            'created': m[6],
            'num_locations': m[7],
            'facebook': m[8],
            'name': m[9],
            'notes': m[10],
            'images': m[11],
            'offers': m[12],
            'locations': m[13],
            'contacts': m[14]
        }

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created': self.created
        }

    def full_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image': self.image,
            'approved': self.approved,
            'coming_soon': self.coming_soon,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created': self.created
        }


class Location(db.Model):
    """
    Location.

    Object for each location per merchant
    """
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='SET NULL'))
    place_id = db.Column(db.String())

    lat = db.Column(db.String())
    lng = db.Column(db.String())
    address = db.Column(db.String())
    address2 = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())
    zip_code = db.Column(db.String())

    phone = db.Column(db.String())

    # Internal checklist
    sticker = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    reviewed = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    visited = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def new(merchant_id):
        """Create new location for given merchant"""
        if merchant_id is not None:
            location = Location(merchant_id=merchant_id)
            db.session.add(location)
            db.session.commit()
            return location

    @staticmethod
    def save(data):
        """Save changes to an location"""
        if data is not None and data.get('id') is not None:
            location = Location.query.get(data['id'])

            location.address = data.get('address')
            location.address2 = data.get('address2')
            location.city = data.get('city')
            location.state = data.get('state')
            location.zip_code = data.get('zip_code')
            location.phone = data.get('phone')

            db.session.commit()
            return location

    def as_dict(self):
        """Dict repr."""
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'place_id': self.place_id,
            'lat': self.lat,
            'lng': self.lng,
            'address': self.address,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'created': self.created,
        }


class Redemption(db.Model):
    """
    Redemption.

    Object for each user's redemption of a deal.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='SET NULL'))
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id', ondelete='SET NULL'))
    day = db.Column(db.String())
    check_in_type = db.Column(db.String())
    value = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def new_redemption(user_id, merchant_id, day, check_in_type, value, offer):
        """Create new redemption."""
        new_r = Redemption(user_id=user_id, merchant_id=merchant_id, day=day, check_in_type=check_in_type, value=value)
        db.session.add(new_r)
        db.session.commit()

        user = User.get(user_id)
        body = None

        # Explode offer for cleaner code
        offer_id = offer.get('id')
        code = offer.get('code')
        code_link = offer.get('code_link')
        offer = offer.get('offer')

        if code:
            body = f"Your code is {code}. Use it to redeem your {offer}!"
            if code_link:
                body = f"Your code is {code}. Head to {code_link} to redeem your {offer}!"
        elif code_link:
            body = f"Head to {code_link} to redeem your discount!"

        # Send SMS message if offer includes a code/code_link
        if user is not None and body is not None:
            send_twilio_sms(body, to=user.phone)

        # Save offer id in user.redeemed_offers for single use offers
        if user and check_in_type == 'specialOffer' and offer_id not in user.redeemed_offers:
            user.redeemed_offers.append(offer_id)

    @staticmethod
    def get_all(user_id):
        """Get all redemptions for given user."""
        sql = text(f"select id, user_id, merchant_id, day, check_in_type, value, created from redemption where user_id "
                   f"= {user_id} order by id;")
        results = db.engine.execute(sql)

        ret = []
        for redemption in results:
            ret.append(Redemption.dict_from_row(redemption))
        return ret

    @staticmethod
    def dict_from_row(row):
        return {
            'id': row[0],
            'user_id': row[1],
            'merchant_id': row[2],
            'day': row[3],
            'check_in_type': row[4],
            'value': row[5],
            'created': row[6]
        }

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'merchant_id': self.merchant_id,
            'day': self.day,
            'check_in_type': self.check_in_type,
            'value': self.value,
            'created': self.created
        }


class Offer(db.Model):
    """
    Offer.

    Merchant offer.
    """
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='SET NULL'))
    hours = db.Column(db.JSON(), default=[], server_default='[]')

    # Offer data
    offer = db.Column(db.String())
    details = db.Column(db.String())

    # SMS code details
    code = db.Column(db.String())
    code_link = db.Column(db.String())

    # Offer values
    deal_limit = db.Column(db.Integer)
    value = db.Column(db.Integer)
    is_bogo = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    single_use = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    happy_hour = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    @staticmethod
    def new(merchant_id):
        """Create new offer for given merchant"""
        if merchant_id is not None:
            offer = Offer(merchant_id=merchant_id)
            db.session.add(offer)
            db.session.commit()
            return offer

    @staticmethod
    def save(data):
        """Save changes to an offer"""
        if data is not None and data.get('id') is not None:
            offer = Offer.query.get(data['id'])

            offer.hours = data.get('hours', [])
            offer.offer = data.get('offer')
            offer.details = data.get('details')
            offer.code = data.get('code')
            offer.code_link = data.get('code_link')
            offer.deal_limit = data.get('deal_limit', 10)
            offer.value = data.get('value', 4)
            offer.is_bogo = data.get('is_bogo')
            offer.single_use = data.get('single_use', False)
            offer.happy_hour = data.get('happy_hour', False)

            db.session.commit()
            return offer

    def as_dict(self):
        """Dict repr."""
        redemptions = Redemption.query.filter_by(offer_id=self.id).count()
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "hours": self.hours,
            "offer": self.offer,
            "details": self.details,
            "code": self.code,
            "code_link": self.code_link,
            "deal_limit": self.deal_limit,
            "value": self.value,
            "is_bogo": self.is_bogo,
            "single_use": self.single_use,
            "happy_hour": self.happy_hour,
            "redemptions": redemptions
        }


class Fundraiser(db.Model):
    """Fundraiser"""
    # Fundraiser Settings
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String())
    team_code = db.Column(db.String())
    base_goal = db.Column(db.Integer)
    incentives = db.Column(db.String())
    start = db.Column(db.Date)
    expiration = db.Column(db.Date)

    # Contact Settings
    contact_name = db.Column(db.String())
    contact_email = db.Column(db.String())
    contact_phone = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())

    active = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    from_form = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    deleted = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def new():
        """Create new fundraiser"""
        fundraiser = Fundraiser(owner_id=current_user.id, incentives=url_for('static', filename='img/incentives.jpg'))
        db.session.add(fundraiser)
        db.session.commit()

        return fundraiser

    @staticmethod
    def save(data):
        """Save changes to a fundraiser"""
        if data is not None and data.get('id') is not None:
            fundraiser = Fundraiser.query.get(data['id'])

            fundraiser.code = data.get('code')
            fundraiser.team_code = data.get('team_code')
            fundraiser.base_goal = data.get('base_goal')
            fundraiser.incentives = data.get('incentives')
            fundraiser.start = data.get('start')
            fundraiser.expiration = data.get('expiration')
            fundraiser.contact_name = data.get('contact_name')
            fundraiser.contact_email = data.get('contact_email')
            fundraiser.contact_phone = data.get('contact_phone')
            fundraiser.city = data.get('city')
            fundraiser.state = data.get('state')
            fundraiser.from_form = data.get('from_form')
            fundraiser.active = data.get('active')

            db.session.commit()
            return fundraiser

    @staticmethod
    def delete(data):
        """Delete fundraiser."""
        if data is not None and data.get('id') is not None:
            fundraiser = Fundraiser.query.get(data['id'])
            fundraiser.deleted = True
            db.session.commit()

    @validates('code')
    def validate_code(self, key, value):
        """Validate Code."""
        return value.lower().replace(" ", "")

    @staticmethod
    def invite_message(name, barcode, m):
        """Generate invite message"""
        body = ''
        if m:
            body = f"{m} "
        body += f"To show {name} your support purchase a 1-year pass to Pass 360, Utah's best discount app." \
                f" Click link to learn more: https://www.passthreesixty.com/fundraising/{barcode}"
        return body

    @staticmethod
    def admin_list_all(offset, limit, search):
        """Get list of all fundraisers"""
        query = "select {0} from fundraiser where deleted = 'f'{1}{2}".format

        body = "id, code, team_code, base_goal, incentives, start, expiration, contact_name, contact_email, " \
               "contact_phone, city, state, active, from_form, owner_id, created, (SELECT json_agg(json_build_object(" \
               "'id', id, 'note', note, 'created', created) ORDER BY fundraiser_note.id DESC) FROM fundraiser_note " \
               "WHERE fundraiser_note.fundraiser_id = fundraiser.id) as notes"

        if search:
            search = f" and (team_code ~* '{search}' or code ~* '{search}')"

        total = f" order by id desc limit {limit} offset {offset * limit}"
        sql = text(query(body, search, total))
        results = db.engine.execute(sql)

        fundraisers = []
        for f in results:
            fundraisers.append(Fundraiser.admin_dict_from_row(f))

        sql = text(query('count(*)', search, ''))
        result = db.engine.execute(sql)
        count = 0
        for row in result:
            count = row[0]

        return fundraisers, count

    @staticmethod
    def admin_dict_from_row(f):
        """Dict from row."""
        return {
            'id': f[0],
            'code': f[1],
            'team_code': f[2],
            'base_goal': f[3],
            'incentives': f[4],
            'start': f[5].strftime('%m/%d/%Y') if f[5] else None,
            'expiration': f[6].strftime('%m/%d/%Y') if f[6] else None,
            'contact_name': f[7],
            'contact_email': f[8],
            'contact_phone': f[9],
            'city': f[10],
            'state': f[11],
            'active': f[12],
            'from_form': f[13],
            'owner_id': f[14],
            'created': f[15],
            'notes': f[16],
        }

    def as_dict(self):
        """Dict repr."""
        return {
            "id": self.id,
            "code": self.code,
            "team_code": self.team_code,
            "base_goal": self.base_goal,
            "incentives": self.incentives,
            "start": self.start,
            "expiration": self.expiration,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "city": self.city,
            "state": self.state,
            "active": self.active,
            "from_form": self.from_form,
            "owner_id": self.owner_id,
            "created": self.created
        }


class FundraiserCode(db.Model):
    """Fundraiser Code"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promo_code.id', ondelete='SET NULL'))
    all_codes = db.Column(db.JSON(), default=[], server_default='[]')
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraiser.id', ondelete='SET NULL'))
    phone = db.Column(db.String())
    name = db.Column(db.String())
    quantity = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('phone')
    def validate_phone(self, key, value):
        """Validate Phone."""
        phone = phone_number_validator(value)
        assert phone is not None
        return value

    @staticmethod
    def new_link(promo_code, user, phone, name):
        """New Fundraiser Code for given promo_code and user"""
        if promo_code and user and phone:
            link = FundraiserCode(user_id=user.id, promo_code_id=promo_code.id, fundraiser_id=user.fundraiser_id,
                                  phone=phone, name=name, quantity=1)
            db.session.add(link)
            db.session.commit()
            return link

    def as_dict(self):
        """Dict repr."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "promo_code_id": self.promo_code_id,
            "all_codes": self.all_codes,
            "fundraiser_id": self.fundraiser_id,
            "phone": self.phone,
            "name": self.name,
            "quantity": self.quantity,
            "created": self.created
        }


class PromoCode(db.Model):
    """
    Promo Code.

    Promotions.
    """
    id = db.Column(db.Integer, primary_key=True)

    barcode = db.Column(db.String())
    code = db.Column(db.String())
    team_code = db.Column(db.String())

    single_use = db.Column(db.Boolean(), nullable=False, default=True, server_default='t')
    active = db.Column(db.Boolean(), nullable=False, default=True, server_default='t')
    redeemed = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    prepaid = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    archived = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    partner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraiser.id', ondelete='SET NULL'))

    # If promo is for six months of access vs 1 year
    six_month = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    # 25% off price point rather than normal price point
    twenty_five = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    expiration = db.Column(db.Date)
    purchased = db.Column(db.DateTime)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def create_fundraiser_code(fid):
        """Create additional fundraiser codes."""
        code = generate_code(8, '#')
        barcode = generate_code(8, 'Aa')

        while len(PromoCode.query.filter_by(code=code).all()):
            code = generate_code(8, '#')

        while len(PromoCode.query.filter_by(code=barcode).all()):
            barcode = generate_code(8, 'Aa')

        new_code = PromoCode(code=code, barcode=barcode, single_use=True, redeemed=False, prepaid=True, active=True,
                             fundraiser_id=fid, purchased=datetime.utcnow())
        db.session.add(new_code)
        db.session.commit()
        return new_code

    @staticmethod
    def fundraiser_codes(fid, uid=None):
        if uid is not None:  # Get personal codes
            sql = text(
                f"SELECT id, user_id, promo_code_id, all_codes, fundraiser_id, phone, \"name\", quantity, created, "
                f"(SELECT prepaid FROM promo_code WHERE promo_code.id = promo_code_id) AS prepaid FROM fundraiser_code"
                f" WHERE user_id = {uid} AND fundraiser_id = {fid} ORDER BY prepaid")
            results = db.engine.execute(sql)

            personal_codes = []
            for row in results:
                personal_codes.append({
                    "id": row[0],
                    "user_id": row[1],
                    "promo_code_id": row[2],
                    "all_codes": row[3],
                    "fundraiser_id": row[4],
                    "phone": row[5],
                    "name": row[6],
                    "quantity": row[7],
                    "created": row[8],
                    "prepaid": row[9]
                })
            return personal_codes
        else:  # Get all fundraiser codes
            codes = PromoCode.query.filter_by(fundraiser_id=fid).order_by(PromoCode.id.desc()).all()
            return [pc.as_dict() for pc in codes]

    def as_dict(self):
        """Dict repr."""
        return {
            "id": self.id,
            "barcode": self.barcode,
            "code": self.code,
            "team_code": self.team_code,
            "single_use": self.single_use,
            "multi_use": not self.single_use,
            "active": self.active,
            "redeemed": self.redeemed,
            "prepaid": self.prepaid,
            "archived": self.archived,
            "partner_id": self.partner_id,
            "fundraiser_id": self.fundraiser_id,
            "six_month": self.six_month,
            "twenty_five": self.twenty_five,
            "expiration": self.expiration,
            "purchased": self.purchased,
            "created": self.created,
        }


class Unsubscriber(db.Model):
    """
    Unsubscriber.

    Keeping track of emails that have requested to unsubscribe.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))


class SmsLog(db.Model):
    """
    Sms Log.

    Twilio message logs.
    """
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String())
    to = db.Column(db.String())
    from_ = db.Column(db.String())
    sid = db.Column(db.String())
    error_code = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'body': self.body,
            'to': self.to,
            'from': self.from_,
            'sid': self.sid,
            'error_code': self.error_code,
            'created': self.created
        }


class Region(db.Model):
    """
    Region.

    Region specific banner data.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    header_uri = db.Column(db.String())
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    button = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    button_size = db.Column(db.Integer)
    button_top = db.Column(db.Integer)
    button_left = db.Column(db.Integer)
    button_color = db.Column(db.String())
    button_url = db.Column(db.String())
    modal_title = db.Column(db.String())
    modal_info = db.Column(db.String())
    button_text = db.Column(db.String())
    button_text_color = db.Column(db.String())
    carousel = db.Column(db.JSON)

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'header_uri': self.header_uri,
            'width': self.width,
            'height': self.height,
            'button': self.button,
            'button_size': self.button_size,
            'button_top': self.button_top,
            'button_left': self.button_left,
            'button_color': self.button_color,
            'button_url': self.button_url,
            'modal_title': self.modal_title,
            'modal_info': self.modal_info,
            'button_text': self.button_text,
            'button_text_color': self.button_text_color,
            'carousel': self.carousel
        }


class DailyActivity(db.Model):
    """
    Daily Activity.

    A record of daily activity for each user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    date = db.Column(db.Date)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    @staticmethod
    def store_daily_activity(user_id, lat=None, lng=None):
        """If daily activity for today is not recorded, create a new record"""
        today = pendulum.today('America/Denver').to_date_string()
        da = DailyActivity.query.filter_by(user_id=user_id, date=today).first()
        if da is None:
            da = DailyActivity(user_id=user_id, date=today)
            db.session.add(da)

        if lat is not None:
            da.latitude = lat
        if lng is not None:
            da.longitude = lng
        db.session.commit()

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date,
            'latitude': self.latitude,
            'longitude': self.longitude
        }


class MagicLink(db.Model):
    """
    Magic Link.

    Record four-digit login codes
    """
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    code = db.Column(db.String())
    # TODO: add uuid hash for security
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def get_message(self):
        """Get four-digit message."""
        return f'Pass360 Code: {self.code}\nUse this code to continue logging into the app.'

    def set_code(self):
        """Generate code."""
        from app.tools import generate_code

        self.code = generate_code(4, '#')
        while MagicLink.query.filter_by(code=self.code).all():
            self.code = generate_code(4, '#')
        db.session.commit()

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'phone': self.phone,
            'user_id': self.user_id,
            'code': self.code,
            'created': self.created
        }


class Activity(db.Model):
    """
    Activity.

    Records of user activity.
    """
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String())
    amount = db.Column(db.Integer)
    code = db.Column(db.String())
    apple = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def cancel(user_id, apple=False):
        """Create a cancellation record."""
        act = Activity(action='Cancellation', user_id=user_id, apple=apple)
        db.session.add(act)
        db.session.commit()

    @staticmethod
    def payment(user_id, amount=0, failed=False):
        """Create a payment record."""
        action = 'Failed Payment' if failed else 'Payment'
        act = Activity(action=action, user_id=user_id, amount=amount)
        db.session.add(act)
        db.session.commit()

    @staticmethod
    def activate(user_id, amount=0, apple=False):
        """Create a payment record."""
        action = 'Activation'
        act = Activity(action=action, user_id=user_id, amount=amount, apple=apple)
        db.session.add(act)
        db.session.commit()

    @staticmethod
    def activate_promo(user_id, fundraiser=False, amount=0):
        """Create a payment record."""
        action = 'Fundraiser' if fundraiser else 'Promo'
        act = Activity(action=action, user_id=user_id, amount=amount)
        db.session.add(act)
        db.session.commit()

    @staticmethod
    def redeem_promo(user_id, code):
        """Create a payment record."""
        act = Activity(action='Redeemed', user_id=user_id, code=code)
        db.session.add(act)
        db.session.commit()

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'action': self.action,
            'amount': self.amount,
            'apple': self.apple,
            'user_id': self.user_id,
            'created': self.created
        }


class Category(db.Model):
    """
    Category.

    Main categories for sorting merchants.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    order = db.Column(db.Integer)
    active = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'active': self.active
        }


class SubCategory(db.Model):
    """
    Sub-Category.

    Sub categories under main categories.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    order = db.Column(db.Integer)
    active = db.Column(db.Boolean(), nullable=False, default=False, server_default='f')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'))

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'active': self.active,
            'category_id': self.category_id
        }


class FoodtruckCheckIn(db.Model):
    """
    Foodtruck Check In.

    Track foodtruck activations
    """
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, default=datetime.utcnow)
    end = db.Column(db.DateTime)
    foodtruck_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='CASCADE'))

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'merchant_id': self.merchant_id
        }


class MerchantContact(db.Model):
    """
    Foodtruck Check In.

    Track foodtruck activations
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    phone = db.Column(db.String())
    business = db.Column(db.String())
    locations = db.Column(db.Integer)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='CASCADE'))

    @staticmethod
    def new(merchant_id):
        """Create new offer for given merchant"""
        if merchant_id is not None:
            contact = MerchantContact(merchant_id=merchant_id)
            db.session.add(contact)
            db.session.commit()
            return contact

    @staticmethod
    def save(data):
        """Save changes to a contact"""
        if data is not None and data.get('id') is not None:
            contact = MerchantContact.query.get(data['id'])

            contact.name = data.get('name', [])
            contact.phone = data.get('phone', [])

            db.session.commit()
            return contact

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'business': self.business,
            'merchant_id': self.merchant_id
        }


class MerchantCategory(db.Model):
    """
    Merchant Category.

    Track categories for merchant.
    """
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='CASCADE'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'))
    sub_category_id = db.Column(db.Integer, db.ForeignKey('sub_category.id', ondelete='CASCADE'))

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'category_id': self.category_id,
            'sub_category_id': self.sub_category_id
        }


class MerchantNote(db.Model):
    """
    Merchant Note.

    Record notes for merchant.
    """
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String())
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id', ondelete='CASCADE'))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'note': self.note,
            'merchant_id': self.merchant_id,
            'created': self.created
        }


class FundraiserNote(db.Model):
    """
    Fundraiser Note.

    Record notes for fundraiser.
    """
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String())
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraiser.id', ondelete='CASCADE'))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'note': self.note,
            'fundraiser_id': self.fundraiser_id,
            'created': self.created
        }


class UserNote(db.Model):
    """
    User Note.

    Record notes for user.
    """
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'note': self.note,
            'user_id': self.user_id,
            'created': self.created
        }


class LocationNote(db.Model):
    """
    Location Note.

    Record notes for a location.
    """
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String())
    location_id = db.Column(db.Integer, db.ForeignKey('location.id', ondelete='CASCADE'))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        """Return dict representation of model."""
        return {
            'id': self.id,
            'note': self.note,
            'location_id': self.location_id,
            'created': self.created
        }

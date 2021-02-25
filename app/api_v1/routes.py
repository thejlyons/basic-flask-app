"""API V1 Endpoints."""
from flask import request, jsonify
from sqlalchemy.orm.attributes import flag_modified
import app.tools
from app.api_v1 import bp
from app.models import db, User, Redemption, PromoCode, Activity, Fundraiser, FundraiserCode, Region, DailyActivity, \
    Merchant, MagicLink, Category, SubCategory, FoodtruckCheckIn
from app import stripe
import pendulum
import os
from datetime import datetime
import app.tools as tools


@bp.route('/push-token', methods=['POST'])
def push_token():
    """Update user's expo push token endpoint."""
    data = request.get_json()

    user = User.get(data.get('id'))
    if user and data.get('push_token') is not None:
        token = data['push_token']
        if isinstance(token, dict) and 'data' in token:
            token = token['data']

        if token is not None and token not in user.expo_push_tokens:
            user.expo_push_tokens.append(token)
            flag_modified(user, "expo_push_tokens")
            db.session.add(user)
            db.session.commit()
    return jsonify({})


@bp.route('/was-used', methods=['POST'])
@bp.route('/redeemed/today', methods=['POST'])
def redeemed_today():
    """Check if deal has already been used."""
    data = request.get_json()

    redemptions = []
    user_id = data.get('user', {}).get('id')
    merchant_id = data.get('merchant', {}).get('id')
    if merchant_id is None:
        merchant_id = data.get('restaurant', {}).get('id')

    if user_id is not None:
        # Find the previous 3am MST
        day_start = pendulum.now('UTC').subtract(days=1, hours=1)
        day_start = day_start.subtract(minutes=day_start.minute, seconds=day_start.second,
                                       microseconds=day_start.microsecond)
        while day_start.hour != 10:
            day_start = day_start.add(hours=1)
        redemptions = [r.as_dict() for r in Redemption.query.filter_by(
            user_id=user_id, merchant_id=merchant_id).filter(
            Redemption.created > day_start).order_by(Redemption.id).all()]

    return jsonify(redemptions)


@bp.route('/use-button', methods=['POST'])
@bp.route('/use-all-day', methods=['POST'])
@bp.route('/use-foodtruck', methods=['POST'])
@bp.route('/use-special-offer', methods=['POST'])
@bp.route('/redeem', methods=['POST'])
def redeem():
    """
    Redeem deal.

    {user: ui.user, restaurant: ui.restaurant, time: today.getHours(), value: offer.value, day: dealDay, offer: offer}
    """
    data = request.get_json()

    check_in_type = None
    if 'use-all-day' in str(request.url_rule):
        check_in_type = 'allDay'
    elif 'use-button' in str(request.url_rule):
        check_in_type = 'happyHour'
    elif 'use-foodtruck' in str(request.url_rule):
        check_in_type = 'foodtruck'
    elif 'use-special-offer' in str(request.url_rule):
        check_in_type = 'specialOffer'

    user_id = data.get('user', {}).get('id')
    merchant_id = data.get('merchant', {}).get('id')
    if merchant_id is None:
        merchant_id = data.get('restaurant', {}).get('id')

    if user_id and merchant_id:
        Redemption.new_redemption(user_id, merchant_id, data.get('day'), data.get('check_in_type', check_in_type),
                                  data.get('value'), data.get('offer'))
    return jsonify({})


@bp.route('/grab-all-uses', methods=['POST'])
@bp.route('/redemption/get', methods=['POST'])
def redemption_get():
    """Get all redemptions for given user."""
    data = request.get_json()

    ret = []
    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        ret = Redemption.get_all(user.id)
    return jsonify(ret)


@bp.route('/grab-user', methods=['POST'])
@bp.route('/user/get', methods=['POST'])
def user_get():
    """Get user dict."""
    data = request.get_json()

    ret = None
    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        ret = user.as_dict()

        if user.promo_id:
            promo = PromoCode.query.get(user.promo_id)
            ret['team_code'] = promo.team_code
        ret['success'] = True
    return jsonify(ret)


@bp.route('/deactivate-iap', methods=['POST'])
@bp.route('/iap/deactivate', methods=['POST'])
def deactivate_iap():
    """Deactivate in-app purchase."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        user.active = False
        user.promo_id = None
        user.promo_timestamp = None
        Activity.cancel(user.id, True)
        db.session.commit()
    return jsonify({})


@bp.route('/webhook/prepaid', methods=['POST'])
def webhook_prepaid():
    """Stripe endpoint for fundraiser purchase webhook."""
    data = request.get_json()

    if data.get('type') == 'checkout.session.completed':
        session = data.get('data', {}).get('object', None)

        cri = session.get('client_reference_id', '').split("|") if session else [None, 0]
        barcode = cri[0]
        quantity = int(cri[1])

        if barcode is not None:
            promo_code = PromoCode.query.filter_by(barcode=barcode).first()
            if promo_code is not None:
                # Activate purchased promo_code to allow redemption
                promo_code.prepaid = True
                promo_code.active = True
                promo_code.purchased = datetime.utcnow()
                db.session.commit()

                fc = FundraiserCode.query.filter_by(promo_code_id=promo_code.id).first()
                if fc:
                    fc.quantity = quantity
                    db.session.commit()

                    promo_codes = [promo_code.code]
                    for x in range(1, quantity):
                        promo_codes.append(PromoCode.create_fundraiser_code(promo_code.fundraiser_id).code)
                    fc.all_codes = promo_codes
                    db.session.commit()

                    body = f"Congratulations your payment has been processed! To redeem your 1-year pass go to the " \
                           f"Pass 360 app and enter your single-use access code: {promo_code.code}"
                    if quantity > 1:
                        new_line = '\n'
                        body = f"Congratulations your payment has been processed! To redeem your 1-year pass go to " \
                               f"the Pass 360 app and enter your single-use access codes:\n{new_line.join(promo_codes)}"

                    app.tools.send_twilio_sms(body, fc.phone, f"+1{os.environ['TWILIO_PHONE']}")
                    return jsonify({"received": True})
    return 'Webhook Error', 400


@bp.route('/handle-subscription-payment-webhook', methods=['POST'])
def webhook_payment():
    """Stripe endpoint for successful payment."""
    data = request.get_json()

    data = data.get('object', {})
    customer_id = data.get('customer')
    if customer_id:
        customer = stripe.Customer.retrieve(customer_id)
        if customer:
            user = User.query.filter_by(stripe_customer=customer.id).first()
            if user:
                user.active = True
                amount = data.get('amount_paid', 0)
                Activity.payment(user.id, amount)

                return jsonify({"done": True})
    return 'Webhook Error', 400


@bp.route('/handle-subscription-payment-failed-webhook', methods=['POST'])
def webhook_payment_failed():
    """Stripe endpoint for successful payment."""
    data = request.get_json()

    data = data.get('object', {})
    customer_id = data.get('customer')
    if customer_id:
        customer = stripe.Customer.retrieve(customer_id)
        if customer:
            user = User.query.filter_by(stripe_customer=customer.id).first()
            if user:
                user.active = True
                amount = data.get('amount_paid', 0)
                Activity.payment(user.id, amount, True)

                return jsonify({"done": True})
    return 'Webhook Error', 400


@bp.route('/cancel-subscription', methods=['POST'])
def cancel_subscription():
    """Cancel subscription."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        if user.stripe_subscription is not None:
            stripe.Subscription.delete(user.stripe_subscription)
        user.active = False
        Activity.cancel(user.id)

    return jsonify({"done": True})


@bp.route('/update-card', methods=['POST'])
def update_card():
    """Update subscription billing method to provided token."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        user.update_card(data.get('token'))
    return jsonify({"done": True})


@bp.route('/iap-activation', methods=['POST'])
def iap_activation():
    """In-app purchase activation."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        user.iap_receipt = data.get('receipt', None)
        user.active = True
        user.promo_id = None
        user.promo_timestamp = None
        user.stripe_customer = None
        if user.stripe_subscription:
            try:
                stripe.Subscription.delete(user.stripe_subscription)
            except:
                pass
        Activity.activate(user.id, 399, True)
    return jsonify({"done": True})


@bp.route('/activate-account', methods=['POST'])
def activate_account():
    """Activate account."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user is not None:
        if user.stripe_customer is None:
            user.create_stripe_customer(data.get('token'))
        else:
            stripe.Customer.create_source(user.stripe_customer, source=data.get('token'))
        user.create_stripe_subscription()
    return jsonify({"done": True})


@bp.route('/handle-promo', methods=['POST'])
def handle_promo():
    """Handle Promo Code."""
    data = request.get_json()
    code = data.get('code')
    user = data['user'] if data.get('user') else {}
    user = User.get(user['id']) if user.get('id') is not None else None
    if code is not None:
        if code == '123456':
            return jsonify({'must_pay': True, 'six_month': False, 'twenty_five': False})
        elif code == 'test25':
            return jsonify({'must_pay': True, 'six_month': False, 'twenty_five': True})
        elif user:
            code = PromoCode.query.filter_by(code=code.lower(), active=True).first()
            if code:
                if code.prepaid and (not code.single_use or not code.redeemed):
                    if user.stripe_subscription:
                        stripe.Subscription.delete(user.stripe_subscription)

                    user.activate_promo(code.id)
                    code.redeemed = True
                    code.active = not code.single_use
                    db.session.commit()

                    Activity.redeem_promo(user.id, code.fundraiser_id is not None)

                    return jsonify({'must_pay': False, 'six_month': code.six_month, 'twenty_five': code.twenty_five})
                elif not code.prepaid and (not code.single_use or (not code.redeemed)):
                    activity = Activity.query.filter_by(user_id=user.id, code=code.code).first()
                    if activity is None:
                        Activity.redeem_promo(user.id, code.code)
                    return jsonify({'must_pay': True, 'six_month': code.six_month, 'twenty_five': code.twenty_five})
                else:
                    return jsonify({'error': 'This code has already been redeemed.'})
    return jsonify({'error': 'Invalid: Please check your code and try again.'})


@bp.route('/activate-promo', methods=['POST'])
def activate_promo():
    """Handle Promo Code."""
    data = request.get_json()
    code = PromoCode.query.filter_by(code=data['code'].lower(), active=True).first() if data.get('code') else None
    user = data['user'] if data.get('user') else {}
    user = User.get(user['id']) if user.get('id') is not None else None
    if code is not None and user is not None:
        if data.get('receipt') and user:
            user.active = True
            user.promo_timestamp = datetime.utcnow()
            user.iap_receipt = data['receipt']
            user.stripe_customer = None
            if code.code == '123456' or code.code == 'test25':
                user.promo_id = 0
            else:
                user.promo_id = code.id
            db.session.commit()

            Activity.activate_promo(user.id, code.fundraiser_id is not None, 3591 if code.twenty_five else 2500)
        else:
            if not code.prepaid and (not code.single_use or not code.redeemed):
                user.create_stripe_customer(data.get('token'))
                amount = 3591 if code.twenty_five else 2500
                try:
                    stripe.Charge.create(
                        amount=amount,
                        currency="usd",
                        source=data.get('token'),
                        description=f"Pass360 Premium Promo code ({code.id}) purchase",
                    )
                except:
                    return jsonify({'error': 'Card could not be charged. Please try again later.'})

                code.redeemed = True
                user.activate_promo(code.id)

                Activity.activate_promo(user.id, code.fundraiser_id is not None, amount)
            else:
                return jsonify({'error': 'This code has already been redeemed.'})
        return jsonify(user.as_dict())
    return jsonify({'error': 'Invalid: Please check your code and try again.'})


@bp.route('/get-card-details', methods=['POST'])
def get_card_details():
    """Get card details"""
    data = request.get_json()
    ret = {'done': True}
    user_id = data.get('user', {}).get('id')
    if user_id:
        user = User.get(user_id)
        if user:
            if user.promo_id is not None:
                pc = PromoCode.query.get(user.promo_id)
                if pc:
                    ret['promo'] = pc.as_dict()
            if user.stripe_customer and 'cus' in user.stripe_customer:
                try:
                    customer = stripe.Customer.retrieve(user.stripe_customer)
                    ret['card'] = customer.get('sources', {}).get('data', [None])[0]
                except:
                    ret['error'] = 'Could not find card data. Please try again later.'
    return jsonify(ret)


@bp.route('/grab-regions', methods=['POST'])
def grab_regions():
    """Get card details."""
    data = request.get_json()
    # TODO: Update this at scale
    regions = [r.as_dict() for r in Region.query.all()]
    latitude, longitude = app.tools.google_api_location(data.get('zip'))
    return jsonify({'regions': regions, 'latitude': latitude, 'longitude': longitude})


@bp.route('/sync-phone', methods=['POST'])
def sync_phone():
    """Sync phone for old users that used an email to log into the app."""
    data = request.get_json()
    user_id = data.get('user', {}).get('id')
    if user_id:
        user = User.get(user_id)
        user.phone = data['user'].get('phone')
        if user.phone is not None:
            db.session.commit()
    return jsonify(user.as_dict())


@bp.route('/grab-deals', methods=['POST'])
@bp.route('/grab-deals-alpha', methods=['POST'])
@bp.route('/merchant/list', methods=['POST'])
def merchant_list(alpha=False):
    """Get a complete list of all merchants including their offers."""
    data = request.get_json()

    if 'grab-deals-alpha' in str(request.url_rule):
        alpha = True

    merchants = []
    user_id = data.get('user', {}).get('id')
    if user_id:
        user = User.get(user_id)
        coords = data.get('location', {}).get('coords')
        lat = None
        lng = None
        if coords is not None:
            lat = coords.get('latitude')
            lng = coords.get('longitude')

        DailyActivity.store_daily_activity(user.id, lat, lng)
        user.update_location(lat, lng)

        if data.get('zip') is not None:
            lat, lng, _, _ = tools.zip_code_data(data['zip'])

        max_dist = user.max_distance if user.max_distance else 25
        merchants = Merchant.list_all(data.get('offset'), max_dist, lat, lng, alpha)
    return jsonify(merchants)


@bp.route('/clear-fundraising', methods=['POST'])
@bp.route('/fundraising/clear', methods=['POST'])
def fundraising_clear():
    """Clear users fundraiser foreign key."""
    data = request.get_json()

    user_id = data.get('user_id')
    if user_id:
        user = User.get(user_id)
        if user:
            user.fundraiser_id = None
            db.session.commit()
    return jsonify({})


@bp.route('/grab-fundraising', methods=['POST'])
@bp.route('/fundraising/get', methods=['POST'])
def fundraising_get():
    """Get users fundraiser data."""
    data = request.get_json()
    ret = {'fundraising': False}

    user_id = data.get('user_id')
    if user_id:
        user = User.get(user_id)
        if user and user.fundraiser_id is not None:
            fundraiser = Fundraiser.query.get(user.fundraiser_id)
            if fundraiser:
                promo_codes = PromoCode.fundraiser_codes(fundraiser.id)
                personal_codes = PromoCode.fundraiser_codes(fundraiser.id, user.id)
                data = {"fundraising": True, "fundraiser": fundraiser.as_dict(), "promo_codes": promo_codes,
                        "personal_codes": personal_codes}
            user.fundraiser_id = None
            db.session.commit()
        data['fundraiser_video'] = os.environ.get('FUNDRAISER_VIDEO_URL')
    return jsonify({})


@bp.route('/set-fundraising', methods=['POST'])
@bp.route('/fundraising/set', methods=['POST'])
def fundraising_set():
    """Set users fundraiser data."""
    data = request.get_json()

    user_id = data.get('user_id')
    if user_id and data.get('code'):
        user = User.get(user_id)
        fundraiser = Fundraiser.query.filter_by(code=data['code']).order_by(Fundraiser.id).first()
        if user and fundraiser:
            user.fundraiser_id = fundraiser.id
            user.name = data.get('name', user.name)
            db.session.commit()
            return jsonify({'fundraising': True, 'fundraiser': fundraiser.as_dict()})
    return jsonify({})


@bp.route('/send-invite-fundraising', methods=['POST'])
@bp.route('/fundraising/invite', methods=['POST'])
def fundraising_invite():
    """Send fundraising invite."""
    data = request.get_json()

    user_id = data.get('user_id')
    phone = tools.phone_number_validator(data.get('phone'))
    name = data.get('name')
    if user_id and phone:
        user = User.get(user_id)
        fundraiser = Fundraiser.query.get(user.fundraiser_id) if user and user.fundraiser_id else None
        if user and fundraiser:
            new_code = PromoCode.create_fundraiser_code(fundraiser.id)
            FundraiserCode.new_link(new_code, user, phone, name)

            tools.send_twilio_sms(Fundraiser.invite_message(user.name, new_code.barcode, data.get('message')), phone)
    return jsonify({})


@bp.route('/fundraising/invite/resend', methods=['POST'])
def fundraising_invite_resend():
    """Send fundraising invite."""
    data = request.get_json()

    user_id = data.get('user_id')
    phone = tools.phone_number_validator(data.get('phone'))
    name = data.get('name')
    if user_id and phone:
        user = User.get(user_id)
        fundraiser = Fundraiser.query.get(user.fundraiser_id) if user and user.fundraiser_id else None
        if user and fundraiser:
            code = FundraiserCode.query.filter_by(user_id=user.id, phone=phone, name=name, fundraiser_id=fundraiser.id)\
                .first()
            if code:
                promo = PromoCode.query.get(code.promo_code_id)
                tools.send_twilio_sms(Fundraiser.invite_message(user.name, promo.barcode, data.get('message')), phone)
    return jsonify({})


@bp.route('/merchant/<merchant_id>', methods=['POST'])
def merchant(merchant_id):
    """Get merchant by given id"""
    merchant = Merchant.query.get(merchant_id)
    if merchant:
        return jsonify(merchant.full_dict())


@bp.route('/four-digit-login', methods=['POST'])
def four_digit_login():
    """Get merchant by given id"""
    data = request.get_json()
    code = data.get('four_digit')
    phone = data.get('phone')
    if code and phone:
        window = pendulum.now('UTC').subtract(hours=1)
        ml = MagicLink.query.filter_by(phone=phone, code=code).filter(MagicLink.created > window).first()
        if ml:
            user = User.query.filter_by(id=ml.user_id, phone=phone).first()
            if user:
                return jsonify(user.as_dict())
    return jsonify({})


@bp.route('/register-phone', methods=['POST'])
def register_phone():
    """Register phone number if new."""
    data = request.get_json()
    phone = tools.phone_number_validator(data.get('phone'))
    if phone:
        user = User.get(phone=phone)
        if not user:
            user = User(phone=phone)
            db.session.add(user)
            db.session.commit()

        ml = MagicLink(phone=phone, user_id=user.id)
        ml.set_code()
        db.session.add(ml)
        db.session.commit()

        tools.send_twilio_sms(ml.get_message(), user.phone)
        return jsonify({'phone': phone})
    return jsonify({})


@bp.route('/category/list', methods=['POST'])
def category_list():
    """Get all categories and sub categories."""
    categories = [c.as_dict() for c in Category.query.filter_by(active=True).order_by(Category.order).all()]
    sub_categories = [s.as_dict() for s in SubCategory.query.filter_by(active=True).order_by(SubCategory.order).all()]
    return jsonify({'categories': categories, 'sub_categories': sub_categories})


@bp.route('/foodtruck', methods=['POST'])
def foodtruck():
    """Send fundraising invite."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user and user.foodtruck_id is not None:
        ft = Merchant.query.get(user.foodtruck_id)
        if ft:
            return jsonify(ft.as_dict())
    return jsonify({'error': 'Could not find foodtruck with given id.'})


@bp.route('/foodtruck/<action>', methods=['POST'])
def foodtruck_action(action):
    """Send fundraising invite."""
    data = request.get_json()

    user_id = data.get('user', {}).get('id')
    user = User.get(user_id) if user_id is not None else None
    if user and user.foodtruck_id is not None:
        ft = Merchant.query.get(user.foodtruck_id)
        if ft:
            if action == 'start':
                ft.latitude = data.get('latitude')
                ft.longitude = data.get('longitude')
                ft.foodtruck = True
                ft.foodtruck_active = True

                check_in = FoodtruckCheckIn(foodtruck_id=ft.id)
                db.session.add(check_in)
            elif action == 'end':
                ft.foodtruck_active = False

                check_in = FoodtruckCheckIn.query.filter_by(foodtruck_id=ft.id, end=None)\
                    .order_by(FoodtruckCheckIn.id.desc()).first()
                if check_in:
                    check_in.end = pendulum.now('UTC')
            db.session.commit()
            return jsonify(ft.as_dict())
    return jsonify({'error': 'Could not find foodtruck with given id.'})


# TODO: Update these on future app update. Being called in app, but needs updated to better practices
@bp.route('/save-user', methods=['POST'])
@bp.route('/user/save/distance', methods=['POST'])
def user_save_distance():
    data = request.get_json()
    user_id = data.get('user', {}).get('id')
    if user_id:
        user = User.get(user_id)
        if user:
            user.max_distance = data.get('user', {}).get('max_distance')
            db.session.commit()
    return jsonify({"done": True})


# TODO: Remove these on future app update. Being called in app, but not for any purpose
@bp.route('/grab-local-bulletins', methods=['POST'])
@bp.route('/grab-uses', methods=['POST'])
def grab_local_bulletins():
    return jsonify([])


@bp.route('/grab-limited-uses', methods=['POST'])
@bp.route('/grab-monthly-affiliate-sign-ups', methods=['POST'])
def grab_monthly_affiliate_sign_ups():
    return jsonify(0)

"""Tools for Pass360."""
from flask import flash, url_for
import re
import pgeocode
from app import twilio_client
import urllib.request
import json
import os
from twilio.base.exceptions import TwilioRestException
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
import random
import string


def push_notify(users, title, message):
    """Send push notification to user."""
    push_tokens = [[]]
    for user in users:
        if user.expo_push_tokens:
            for token in user.expo_push_tokens:
                push_tokens[-1].append(token)
                if len(push_tokens[-1]) > 98:
                    push_tokens.append([])

    for group in push_tokens:
        body = [{
            "to": token,
            "title": title,
            "body": message
        } for token in group]
        notify(body)


def notify(body):
    """Send push notification."""
    url = "https://exp.host/--/api/v2/push/send"

    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    json_data = json.dumps(body)
    json_data_bytes = json_data.encode('utf-8')
    req.add_header('Content-Length', len(json_data_bytes))
    response = urllib.request.urlopen(req, json_data_bytes)


def send_twilio_sms(body, to, from_=f"+1{os.environ.get('TWILIO_PHONE')}"):
    """Send twilio sms and track count in DB as UserSMS()"""
    from app.models import db, SmsLog

    code = None
    sid = None
    try:
        m = twilio_client.messages.create(body=body, to=to, from_=from_)
        sid = m.sid
    except TwilioRestException as e:
        code = e.code

    sms = SmsLog(body=body, to=to, from_=from_, error_code=code, sid=sid)
    db.session.add(sms)
    db.session.commit()


def phone_number_validator(pnumbers=""):
    if pnumbers is None:
        return None
    numbers = list(map(format_phone_number, pnumbers.split("/")))
    first_valid = next(filter(phone_numbers_filter, numbers), None)
    return first_valid[2:] if first_valid else None


def format_phone_number(phone=""):
    phone = ''.join(x for x in phone if x.isdigit())
    if len(phone) == 10:
        phone = f"+1{phone}"
    elif len(phone) == 11 and phone.startswith("1"):
        phone = f"+{phone}"
    else:
        phone = ''

    return phone


def phone_numbers_filter(phone):
    if phone != '':
        try:
            input_number = phonenumbers.parse(phone)
            if phonenumbers.is_valid_number(input_number):
                res = twilio_client.lookups.phone_numbers(phone).fetch(type=['carrier'])
                if res.carrier and res.carrier.get('type') and res.carrier.get('type') in ['mobile']:
                    return True
        except NumberParseException:
            return False

    return False


def generate_code(num_chars, chars):
    """Generate a code of given length with given characters

    COPY public.pitch_step
    """
    selected_chars = ''
    if 'a' in chars:
        selected_chars += string.ascii_lowercase
    if 'A' in chars:
        selected_chars += string.ascii_uppercase
    if '#' in chars:
        selected_chars += string.digits
    if '!' in chars:
        selected_chars += string.punctuation

    return ''.join(random.choice(selected_chars) for i in range(num_chars))


def zip_code_data(zip_code=None):
    """Get lat and lng for zip code"""
    lat = None
    lng = None
    city = None
    state = None
    if zip_code is not None:
        nomi = pgeocode.Nominatim('us')
        data = nomi.query_postal_code(zip_code)
        lat = data.latitude
        lng = data.longitude
        city = data.place_name
        state = data.state_name
    return lat, lng, city, state


def zip_code_dist(zip1, zip2):
    """Get distance between two zip codes"""
    dist = pgeocode.GeoDistance('us')
    return dist.query_postal_code(zip1, zip2)


def google_api_location(zip_code=None):
    """Get location data from given zip by querying google maps api."""
    latitude = None
    longitude = None
    if zip_code is not None:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&key=" \
              f"{os.environ.get('GOOGLE_API_KEY')}"

        req = urllib.request.urlopen(url)
        response = json.loads(req.read().decode())

        location = response.get('results', [None])[0]
        if location is not None:
            location = location.get('geometry', {}).get('location', {'lat': None, 'lng': None})
            latitude = location['lat']
            longitude = location['lng']
    return latitude, longitude

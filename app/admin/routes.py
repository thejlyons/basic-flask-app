"""Admin Endpoints."""
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from app.admin import bp
from app.models import db, Merchant, MerchantNote, Offer, Location, MerchantContact, Fundraiser, FundraiserNote, \
    User, UserNote, LocationNote
import app.tools as tools


@bp.route('/')
@login_required
def home():
    """Home."""
    return render_template('admin/home.html')


@bp.route('/merchants')
@login_required
def merchants():
    """Merchants."""
    return render_template('admin/merchants.html')


@bp.route('/merchant/<action>', methods=['POST'])
@login_required
def merchant(action):
    """
    Manage merchants endpoint.

    action = any(list-all, new, save, delete, note, delete-note)
    """

    data = request.get_json()
    if action == 'list-all':
        merchants, count = Merchant.admin_list_all(data.get('offset', 0), data.get('limit', 25), data.get('search', ''))
        return jsonify({'merchants': merchants, 'count': count})
    elif action == 'new':
        return jsonify({'merchant': Merchant.new().as_dict()})
    elif action == 'save':
        Merchant.save(data.get('merchant'))
        return jsonify({'success': True})
    elif action == 'delete':
        Merchant.delete(data.get('merchant'))
        return jsonify({'success': True})
    elif action == 'note':
        if data.get('merchant_id') is not None:
            note = MerchantNote(note=data.get('note'), merchant_id=data['merchant_id'])
            db.session.add(note)
            db.session.commit()
            return jsonify({'note': note.as_dict()})
    elif action == 'delete-note':
        if data.get('note') is not None and data['note'].get('id') is not None:
            note = MerchantNote.query.get(data['note']['id'])
            db.session.delete(note)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'location-note':
        if data.get('location_id') is not None:
            note = LocationNote(note=data.get('note'), location_id=data['location_id'])
            db.session.add(note)
            db.session.commit()
            return jsonify({'note': note.as_dict()})
    elif action == 'location-delete-note':
        if data.get('note') is not None and data['note'].get('id') is not None:
            note = LocationNote.query.get(data['note']['id'])
            db.session.delete(note)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'offer-new':
        offer = Offer.new(data.get('merchant_id'))
        if offer is not None:
            return jsonify({'offer': offer.as_dict()})
    elif action == 'offer-save':
        offer = Offer.save(data.get('offer'))
        if offer is not None:
            return jsonify({'offer': offer.as_dict()})
    elif action == 'offer-delete':
        offer_id = data.get('offer', {}).get('id')
        if offer_id is not None:
            offer = Offer.query.get(offer_id)
            db.session.delete(offer)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'location-new':
        location = Location.new(data.get('merchant_id'))
        if location is not None:
            return jsonify({'location': location.as_dict()})
    elif action == 'location-save':
        location = Location.save(data.get('location'))
        if location is not None:
            return jsonify({'location': location.as_dict()})
    elif action == 'location-delete':
        location_id = data.get('location', {}).get('id')
        if location_id is not None:
            location = Location.query.get(location_id)
            db.session.delete(location)
            db.session.commit()
            return jsonify({'success': True})
    elif action == 'contact-new':
        contact = MerchantContact.new(data.get('merchant_id'))
        if contact is not None:
            return jsonify({'contact': contact.as_dict()})
    elif action == 'contact-save':
        contact = MerchantContact.save(data.get('contact'))
        if contact is not None:
            return jsonify({'contact': contact.as_dict()})
    elif action == 'contact-delete':
        contact_id = data.get('contact', {}).get('id')
        if contact_id is not None:
            contact = MerchantContact.query.get(contact_id)
            db.session.delete(contact)
            db.session.commit()
            return jsonify({'success': True})
    return jsonify({}), 400


@bp.route('/users')
@login_required
def users():
    """Users."""
    return render_template('admin/users.html')


@bp.route('/user/<action>', methods=['POST'])
@login_required
def user(action):
    """
    Manage users endpoint.

    action = any(list-all, new, save, delete, note, delete-note)
    """

    data = request.get_json()
    if action == 'list-all':
        users, count = User.admin_list_all(data.get('offset', 0), data.get('limit', 25), data.get('search', ''))
        return jsonify({'users': users, 'count': count})
    elif action == 'active':
        user_id = data.get('user', {}).get('id')
        if user_id is not None:
            user = User.get(user_id)
            user.active = not user.active
            db.session.commit()
            return jsonify({'user': user.as_dict()})
    elif action == 'note':
        if data.get('user_id') is not None:
            note = UserNote(note=data.get('note'), user_id=data['user_id'])
            db.session.add(note)
            db.session.commit()
            return jsonify({'note': note.as_dict()})
    elif action == 'delete-note':
        if data.get('note') is not None and data['note'].get('id') is not None:
            note = UserNote.query.get(data['note']['id'])
            db.session.delete(note)
            db.session.commit()
            return jsonify({'success': True})
    return jsonify({}), 400


@bp.route('/fundraisers')
@login_required
def fundraisers():
    """Fundraisers."""
    return render_template('admin/fundraisers.html')


@bp.route('/fundraiser/<action>', methods=['POST'])
@login_required
def fundraiser(action):
    """
    Manage fundraisers endpoint.

    action = any(list-all, new, save, delete, note, delete-note)
    """

    data = request.get_json()
    if action == 'list-all':
        fundraisers, count = Fundraiser.admin_list_all(data.get('offset', 0), data.get('limit', 25),
                                                       data.get('search', ''))
        return jsonify({'fundraisers': fundraisers, 'count': count})
    elif action == 'new':
        return jsonify({'fundraiser': Fundraiser.new().as_dict()})
    elif action == 'save':
        Fundraiser.save(data.get('fundraiser'))
        return jsonify({'success': True})
    elif action == 'delete':
        Fundraiser.delete(data.get('fundraiser'))
        return jsonify({'success': True})
    elif action == 'note':
        if data.get('fundraiser_id') is not None:
            note = FundraiserNote(note=data.get('note'), fundraiser_id=data['fundraiser_id'])
            db.session.add(note)
            db.session.commit()
            return jsonify({'note': note.as_dict()})
    elif action == 'delete-note':
        if data.get('note') is not None and data['note'].get('id') is not None:
            note = FundraiserNote.query.get(data['note']['id'])
            db.session.delete(note)
            db.session.commit()
            return jsonify({'success': True})
    return jsonify({}), 400

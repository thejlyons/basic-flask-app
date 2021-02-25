"""Index Endpoints."""
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from app.index import bp
from app.index.forms import FundraisingForm, MerchantForm
from app.models import db, Fundraiser, MerchantContact, Merchant
import app.tools as tools


@bp.route('/')
@bp.route('/index')
@bp.route('/home')
def index():
    """Home."""
    return render_template('index/index.html')


@bp.route('/fundraising')
def fundraising():
    """Fundraising."""
    form = FundraisingForm()
    return render_template('index/fundraising.html', form=form)


@bp.route('/fundraising/submit', methods=['POST'])
def fundraising_submit():
    """Fundraising Submit Form."""
    form = FundraisingForm()
    if form.is_submitted() and form.validate_on_submit():
        fundraiser = Fundraiser(contact_name=form.fullname.data, contact_email=form.email.data, city=form.city.data,
                                contact_phone=form.phone.data, state=form.state.data, team_code=form.organization.data,
                                base_goal=form.base_goal.data, start=form.start.data, from_form=True)
        db.session.add(fundraiser)
        db.session.commit()
        flash("Form successfully submitted. We'll be in touch shortly!")
        return redirect(url_for('index.fundraising'))
    return render_template('index/fundraising.html', form=form, error=True)


@bp.route('/merchants')
def merchants():
    """Merchants."""
    form = MerchantForm()
    return render_template('index/merchants.html', form=form)


@bp.route('/merchants/submit', methods=['POST'])
def merchants_submit():
    """Merchant Submit Form."""
    form = MerchantForm()
    if form.is_submitted() and form.validate_on_submit():
        merchant = Merchant(name=form.business.data)
        db.session.add(merchant)
        db.session.commit()

        mc = MerchantContact(name=form.fullname.data, phone=form.phone.data, business=form.business.data,
                             locations=form.locations.data, merchant_id=merchant.id)
        db.session.add(mc)
        db.session.commit()
        flash("Form successfully submitted. We'll be in touch shortly!")
        return redirect(url_for('index.merchants'))
    return render_template('index/merchants.html', form=form, error=True)


@bp.route('/contact')
def contact():
    """Contact."""
    return render_template('index/contact.html')

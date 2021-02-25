from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, Email, Optional, EqualTo


class FundraisingForm(FlaskForm):
    """Fundraising Form"""

    def validate_phone(form, field):
        """Validate phone number."""
        from app.tools import phone_number_validator
        phone = phone_number_validator(field.data)
        if phone is None:
            raise ValidationError("Invalid phone number")

    fullname = StringField('First and Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    organization = StringField('Name of Fundraising Organization', validators=[DataRequired()])
    base_goal = StringField('Monetary Goal', validators=[Optional()])
    start = StringField('Estimated Fundraising Start Date', validators=[Optional()],
                        render_kw={"placeholder": "DD/MM/YYYY"})
    submit = SubmitField('Submit')


class MerchantForm(FlaskForm):
    """Merchant Form"""

    def validate_phone(form, field):
        """Validate phone number."""
        from app.tools import phone_number_validator
        phone = phone_number_validator(field.data)
        if phone is None:
            raise ValidationError("Invalid phone number")

    fullname = StringField('First and Last Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    business = StringField('Name of Business', validators=[DataRequired()])
    locations = IntegerField('Number of Locations', validators=[DataRequired()])
    submit = SubmitField('Submit')

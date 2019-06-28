from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError, SelectField
from wtforms.validators import DataRequired, Email, Optional, EqualTo


class LoginForm(FlaskForm):
    """Login Form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password')
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """Register Form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class UnsubscribeForm(FlaskForm):
    """Unsubscribe Form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Unsubscribe')


class ResetPasswordRequestForm(FlaskForm):
    """Reset Password Request Form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset')


class ResetPasswordForm(FlaskForm):
    """Reset Password Form"""
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

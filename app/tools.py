"""Tools for DistroTeam."""
from flask import flash, url_for


def test_tools(message):
    """Test for setup purposes."""
    flash(message)


def get_landing_page(user):
    """Return url for landing depending on type of user."""
    if user.admin:
        flash("Welcome, admin")
    elif user.influencer:
        flash("Welcome, influencer")
    else:
        flash("Welcome")
    return url_for('index')

import os
import base64
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """General Settings."""
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMINS = [email.strip() for email in os.environ['ADMIN_EMAILS'].split(',')]
    SECRET_KEY = 'temp-secret-key-here'
    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = base64.b64decode(os.environ.get('SECRET_KEY'))
    S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(os.environ.get("S3_BUCKET_NAME"))


class ProductionConfig(Config):
    """Production Settings"""
    DEBUG = False


class StagingConfig(Config):
    """Staging Settings"""
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """Dev Settings"""
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """Testing Settings"""
    TEST_DB = 'test.db'
    TESTING = True
    WTF_CSRF_ENABLED = False
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(basedir, TEST_DB))


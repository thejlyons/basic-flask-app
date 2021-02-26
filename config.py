"""Pass360 Config"""
__version__ = '0.1.2'

import os
import hashlib

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """General Settings."""
    m = hashlib.md5()
    VERSION_CODE = __version__
    m.update(VERSION_CODE.encode('utf-8'))
    VERSION = str(int(m.hexdigest(), 16))[0:12]

    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMINS = [email.strip() for email in os.environ['ADMIN_EMAILS'].split(',')]
    ADMIN_TOKENS = [token.strip() for token in os.environ['ADMIN_EXPO_TOKEN'].split(',')]

    SECRET_KEY = os.environ.get('SECRET_KEY', 'temp-secret-key-here')
    S3_SECRET = os.environ.get("S3_SECRET")
    S3_ACCESS = os.environ.get("S3_ACCESS")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(S3_BUCKET_NAME)

    REDIS_URL = os.environ.get("REDIS_URL")
    CELERY_BROKER_URL = REDIS_URL if REDIS_URL else 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = REDIS_URL if REDIS_URL else 'redis://localhost:6379'

    STRIPE_SUBSCRIPTION_ID = os.environ.get('STRIPE_SUBSCRIPTION_ID', 'mealpass')


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


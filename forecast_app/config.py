# TODO: Figure a better way to handle these secrets

try:
    from forecast_app.secret_config import (
        ADMIN_USER,
        ADMIN_PASSWORD,
        SECRET_KEY,
        EMAIL,
    )
except ImportError:
    # It's okay if this isn't defined for local development and testing
    ADMIN_USER = None
    ADMIN_PASSWORD = None
    SECRET_KEY = None
    EMAIL = None

SECRET_VARS = ["ADMIN_USER", "ADMIN_PASSWORD", "SECRET_KEY", "DOMAIN", "EMAIL"]


class abstract_attribute(object):
    def __get__(self, obj, type):
        raise NotImplementedError("This attribute was not set in a subclass")


class Config(object):
    TESTING = False
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "admin"
    SECRET_KEY = "secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OUTPUT_DIR = "forecast_app/static/output"
    UPLOAD_FOLDER = "forecast_app/static/uploads"
    PORT = 5000
    WORKERS = 1
    DEBUG = True
    CERT_DIR = None
    EMAIL = "kevinrmcelwee@gmail.com"
    DOMAIN = "coopforecast.com"


class ProductionConfig(Config):
    NAME = "prod"
    ADMIN_USER = ADMIN_USER
    ADMIN_PASSWORD = ADMIN_PASSWORD
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/prod.db"
    PORT = 443
    WORKERS = 4
    DEBUG = False
    # TODO: set domain
    CERT_DIR = f"/etc/letsencrypt/live/{Config.DOMAIN}"


class DevelopmentConfig(Config):
    NAME = "dev"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/dev.db"


class TestingConfig(Config):
    NAME = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/test.db"
    TESTING = True
    OUTPUT_DIR = "forecast_app/tests/tmp_output"
    UPLOAD_DIR = "forecast_app/tests/tmp_upload"


configs = [TestingConfig, ProductionConfig, DevelopmentConfig]
config_map = {config.NAME: config for config in configs}

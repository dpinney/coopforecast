from datetime import datetime

try:
    from forecast_app.secret_config import (
        ADMIN_USER,
        ADMIN_PASSWORD,
        SECRET_KEY,
    )
except ImportError:
    # It's okay if this isn't defined for local development and testing
    ADMIN_USER = None
    ADMIN_PASSWORD = None
    SECRET_KEY = None

SECRET_VARS = ["ADMIN_USER", "ADMIN_PASSWORD", "SECRET_KEY", "DOMAIN", "EMAIL"]

# GLOBAL CONFIGS
EMAIL = "admin@coopforecast.com"
DOMAIN = "coopforecast.com"


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
    UPLOAD_DIR = "forecast_app/static/uploads"
    PORT = 5000
    WORKERS = 1
    DEBUG = True
    CERT_DIR = None
    EMAIL = EMAIL
    DOMAIN = DOMAIN
    GUNICORN_PATH = "gunicorn"
    REDIRECT_PORT = 4000
    EPOCHS = 1
    LOAD_COL = "kw"
    TEMP_COL = "tempc"
    HOUR_COL = "hour"
    DATE_COL = "date"
    ASOS_STATION = "TQE"
    TIMEZONE = "America/Chicago"
    # Get weather codes and stations here: https://mesonet.agron.iastate.edu/request/download.phtml
    # Note for USA stations (beginning with a K) you must NOT include the 'K'
    #  WARNING: Ensure that both the station and timezone are updated. There's no indication
    #    otherwise when the timezone is incorrect
    NWS_CODE = "OAX/72,83"
    # To get the NWS code, first use "https://api.weather.gov/points/{lat},{lon}" to get metadata
    #  from there, the "forecastHourly" property contains the code you need.
    #  Please use the form "STATION/##,##"
    EARLIEST_SYNC_DATE = datetime(2016, 1, 1)


class ProductionConfig(Config):
    NAME = "prod"
    ADMIN_USER = ADMIN_USER
    ADMIN_PASSWORD = ADMIN_PASSWORD
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/prod.db"
    PORT = 443
    WORKERS = 4
    DEBUG = False
    CERT_DIR = f"/etc/letsencrypt/live/{DOMAIN}"
    # NOTE: systemctl wouldn't recognize gunicorn on the path
    GUNICORN_PATH = "/home/ubuntu/.local/bin/gunicorn"
    REDIRECT_PORT = 80
    EPOCHS = 10


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

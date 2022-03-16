"""App configurations for different environments. Imports from secret_config.py for all sensitive info."""

from datetime import datetime

# Import the secret configurations
try:
    from forecast_app.secret_config import ADMIN_PASSWORD, ADMIN_USER, SECRET_KEY
except ImportError:
    # It's okay if this isn't defined for local development and testing
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "admin"
    SECRET_KEY = "secret"

# Email and domain need to be set here so that they can be easily imported in bash scripts
EMAIL = "admin@coopforecast.com"
DOMAIN = "burtcoppd.coopforecast.com"


class Config(object):
    """Base configuration."""

    """Flask configuration."""
    TESTING = False
    DEBUG = True

    """Database configuration."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    """Local path to store user content"""
    OUTPUT_DIR = "forecast_app/user-content/output"
    UPLOAD_DIR = "forecast_app/user-content/uploads"

    """Web serving configuration"""
    PORT = 5000
    REDIRECT_PORT = 4000
    WORKERS = 1  # Number of processes to use for Gunicorn
    # Needs to be explicitly defined since systemctl wouldn't recognize an implicit path on prod
    GUNICORN_PATH = "gunicorn"

    """Secrets config"""
    ADMIN_USER = ADMIN_USER
    ADMIN_PASSWORD = ADMIN_PASSWORD
    SECRET_KEY = SECRET_KEY

    """SSL config (for production)"""
    CERT_DIR = f"/etc/letsencrypt/live/{DOMAIN}"
    EMAIL = EMAIL
    DOMAIN = DOMAIN

    """Data ingest config. Columns in the expected CSV file uploads."""
    LOAD_COL = "kw"
    TEMP_COL = "tempc"
    HOUR_COL = "hour"
    DATE_COL = "date"

    """Machine learning config"""
    EPOCHS = 1
    HOURS_PRIOR = 24

    """Logo path"""
    LOGO_PATH = "img/demo.png"

    """External API config"""
    # Info for data syncing with external APIs
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

    """Required configurations in subclasses"""
    NAME = None
    SQLALCHEMY_DATABASE_URI = None


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    NAME = "prod"

    SQLALCHEMY_DATABASE_URI = "sqlite:///db/prod.db"

    PORT = 443
    REDIRECT_PORT = 80
    WORKERS = 4
    GUNICORN_PATH = "/home/ubuntu/.local/bin/gunicorn"

    EPOCHS = 75

    LOGO_PATH = "img/burt.png"


class DevelopmentConfig(Config):
    """Development configuration."""

    NAME = "dev"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/dev.db"


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True

    NAME = "test"

    SQLALCHEMY_DATABASE_URI = "sqlite:///db/test.db"

    OUTPUT_DIR = "forecast_app/tests/user-content/tmp_output"
    UPLOAD_DIR = "forecast_app/tests/user-content/tmp_upload"


class DemoConfig(Config):
    # FREEZE CONFIGS
    NAME = "demo"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/demo.db"
    FREEZER_DESTINATION = "../build"
    FREEZER_IGNORE_MINIMAL_MIMETYPE_WARNINGS = True
    FREEZER_RELATIVE_URLS = True  # False?


configs = [TestingConfig, ProductionConfig, DevelopmentConfig, DemoConfig]
config_map = {config.NAME: config for config in configs}
SECRET_VARS = ["ADMIN_USER", "ADMIN_PASSWORD", "SECRET_KEY"]

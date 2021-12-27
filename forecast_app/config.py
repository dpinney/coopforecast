try:
    from forecast_app.secret_config import ADMIN_USER, ADMIN_PASSWORD, SECRET_KEY
except ImportError:
    # It's okay if this isn't defined for local development and testing
    ADMIN_USER = None
    ADMIN_PASSWORD = None
    SECRET_KEY = None


class Config(object):
    TESTING = False
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "admin"
    SECRET_KEY = "secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MODEL_OUTPUT_DIR = "forecast_app/static/output"
    UPLOAD_FOLDER = "forecast_app/static/uploads"


class ProductionConfig(Config):
    ADMIN_USER = ADMIN_USER
    ADMIN_PASSWORD = ADMIN_PASSWORD
    SECRET_KEY = SECRET_KEY
    # TODO: Use better database location
    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/dev.db"


class DevelopmentConfig(Config):
    # TODO: Use better database location
    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/dev.db"


class TestingConfig(Config):
    # TODO: Use better database location
    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/test.db"
    TESTING = True
    # TODO: set upload folder

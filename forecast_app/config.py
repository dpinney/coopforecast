from forecast_app.secret_config import ADMIN_USER, ADMIN_PASSWORD, SECRET_KEY
import tempfile


class Config(object):
    TESTING = False
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "admin"
    SECRET_KEY = "secret"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MODEL_OUTPUT_DIR = "forecast_app/static/output/"


class ProductionConfig(Config):
    ADMIN_USER = ADMIN_USER
    ADMIN_PASSWORD = ADMIN_PASSWORD
    SECRET_KEY = SECRET_KEY


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/test.db"
    UPLOAD_FOLDER = "forecast_app/static/uploads"


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/testing.db"
    TESTING = True
    # TODO: set upload folder

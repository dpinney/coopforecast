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
    PORT = 5000
    WORKERS = 1
    DEBUG = True


class ProductionConfig(Config):
    NAME = "prod"
    ADMIN_USER = ADMIN_USER
    ADMIN_PASSWORD = ADMIN_PASSWORD
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/prod.db"
    PORT = 443
    WORKERS = 5
    DEBUG = False


class DevelopmentConfig(Config):
    NAME = "dev"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/dev.db"


class TestingConfig(Config):
    NAME = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db/test.db"
    TESTING = True
    OUTPUT_DIR = "forecast_app/tests/tmp_output"
    # TODO: set upload folder


configs = [TestingConfig, ProductionConfig, DevelopmentConfig]
config_map = {config.NAME: config for config in configs}

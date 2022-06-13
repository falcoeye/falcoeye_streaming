import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False

    # flask restx settings
    SWAGGER_UI_DOC_EXPANSION = "list"

    BACKEND_SERVER_NAME = os.environ.get("BACKEND_SERVER_NAME", "http://127.0.0.1:5000")


class DevelopmentConfig(Config):
    DEBUG = True
    # Add logger


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    # In-memory SQLite for testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPRARY_DATA_PATH = f"{basedir}/data/"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig,
)

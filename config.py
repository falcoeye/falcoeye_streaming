import os
from datetime import timedelta
import fsspec
basedir = os.path.abspath(os.path.dirname(__file__))
from k8s import FalcoServingKube

class Config:
    DEBUG = False

    # flask restx settings
    SWAGGER_UI_DOC_EXPANSION = "list"
    BACKEND_HOST = os.environ.get("BACKEND_HOST", "http://127.0.0.1:5000")

    # file system interface
    FS_PROTOCOL = os.environ.get("FS_PROTOCOL", "file")
    DEPLOYMENT = os.environ.get("DEPLOYMENT","local")

    SERVICES = {
        "falcoeye-backend": {
            "env": "BACKEND_HOST",
            "k8s": None
        }
    }
    if DEPLOYMENT == "k8s":
        SERVICES["falcoeye-backend"]["k8s"] = FalcoServingKube("falcoeye-backend")
    
    if FS_PROTOCOL in ("gs", "gcs"):
        import gcsfs
        FS_TOKEN = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "cloud")
        FS_BUCKET = os.environ.get("FS_BUCKET", "")
        FS_PROJECT = os.environ.get("FS_PROJECT", "falcoeye")
        DEPLOYMENT = os.environ.get("DEPLOYMENT")
        FS_OBJ = gcsfs.GCSFileSystem(project=FS_PROJECT, token=FS_TOKEN)
        FS_IS_REMOTE = True
        TEMPORARY_DATA_PATH = os.environ.get(
            "TEMPORARY_DATA_PATH", f"{FS_BUCKET}/falcoeye-temp/data/"
        )

    elif FS_PROTOCOL == "file":
        FS_OBJ = fsspec.filesystem(FS_PROTOCOL)
        FS_IS_REMOTE = False
        TEMPORARY_DATA_PATH = os.environ.get(
            "TEMPORARY_DATA_PATH", f"{basedir}/tests/falcoeye-temp/data/"
        )
    else:
        raise SystemError(f"support for {FS_PROTOCOL} has not been added yet")



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

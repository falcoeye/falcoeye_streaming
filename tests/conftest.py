import pytest
import logging
from app import create_app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

@pytest.fixture
def app():
    app = create_app("testing")
    app.testing = True
    return app


@pytest.fixture
def client(app):
    with app.app_context():
        with app.test_client() as client:
            yield client


@pytest.fixture
def harbour_camera():
    return {
        "streaming_type": "StreamingServer",
        "url": "https://www.youtube.com/watch?v=NwWgOilQuzw&t=4s",
    }

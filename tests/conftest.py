import pytest

from app import create_app


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

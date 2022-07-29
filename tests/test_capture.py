import json
import time
from unittest import mock


def mocked_streamer_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def response(self):
            return self.json_data, self.status_code

    return MockResponse(
        {"status": True, "message": "Change status has been handled"}, 200
    )


def loop_until_finished(client, reg_key, time_before_kill, sleep_time):

    resp = client.get(
        f"/api/capture/{reg_key}",
    )

    status = resp.json.get("capture_status")
    elapsed = 0
    while status == "STARTED":
        print(status)
        time.sleep(sleep_time)
        if elapsed > time_before_kill:
            break

        resp = client.get(f"/api/capture/{reg_key}")
        status = resp.json.get("capture_status")
        elapsed += sleep_time


@mock.patch("app.api.capture.service.requests.post", side_effect=mocked_streamer_post)
def test_capture_image(mock_post, client, harbour_camera):
    registry_key = "test_picture"
    data = {
        "registry_key": registry_key,
        "camera": harbour_camera,
        "output_path": "tests/media/test.jpg",
        "capture_type": "image",
    }
    resp = client.post("/api/capture", data=json.dumps(data))

    assert resp.status_code == 200
    assert resp.json.get("message") == "Capture request initiated"

    time_before_kill = 100
    sleep_time = 4
    loop_until_finished(client, registry_key, time_before_kill, sleep_time)


@mock.patch("app.api.capture.service.requests.post", side_effect=mocked_streamer_post)
def test_capture_video(mock_post, client, harbour_camera):
    registry_key = "test_picture"
    data = {
        "registry_key": registry_key,
        "camera": harbour_camera,
        "output_path": "tests/media/test.mp4",
        "capture_type": "video",
        "length": 3,
    }
    resp = client.post("/api/capture", data=json.dumps(data))

    assert resp.status_code == 200
    assert resp.json.get("message") == "Capture request initiated"

    time_before_kill = 100
    sleep_time = 3
    loop_until_finished(client, registry_key, time_before_kill, sleep_time)

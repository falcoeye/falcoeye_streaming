import json
import os
import threading

import requests
from falcoeye_core.io import source
from flask import current_app
from PIL import Image

from app.utils import internal_err_resp, message
from config import config_by_name


class CaptureService:
    required_fields = [
        ("registry_key", str),
        ("url", str),
        ("stream_provider", str),
        ("resolution", str),
        ("output_path", str),
    ]
    @staticmethod
    def capture_(
        registry_key,
        url,
        stream_provider,
        resolution,
        output_path
    ):
        image = source.capture_image(url, stream_provider)
        if image is not None:
            Image.fromarray(image).save(output_path)
            resp = message(True, "Image has been captured.")
            resp["registry_key"] = registry_key
            resp["capture_status"] = "CAPTURED"
        else:
            resp = message(False, "Couldn't capture image. No stream found")
            resp["registry_key"] = registry_key
            resp["capture_status"] = "FAILEDTOCAPUTRE"

        try:
            backend_server = config_by_name[os.environ.get("FLASK_CONFIG","development")].BACKEND_SERVER_NAME
            postback_url = f"http://{backend_server}/api/capture/status/{registry_key}"
            rv = requests.post(postback_url, data=json.dumps(resp),headers = {
                "Content-type": "application/json"})
            #"X-API-KEY":access_token})
        except requests.exceptions.ConnectionError:
            print(f"Warning: failed to inform backend server ({backend_server}) for change in the status of: {registry_key} due to ConnectionError")
        except requests.exceptions.Timeout:
            print(f"Warning: failed to inform backend server ({backend_server}) for change in the status of: {registry_key} due to Timeout")
        except requests.exceptions.HTTPError:
            print(f"Warning: failed to inform backend server ({backend_server}) for change in the status of: {registry_key} due to HTTPError")



    @staticmethod
    def capture(data):
        parsed_data = []
        for field, ftype in CaptureService.required_fields:
            if field not in data:
                return internal_err_resp()
            parsed_data.append(ftype(data[field]))

        try:
            a_thread = threading.Thread(
                target=CaptureService.capture_,
                args=parsed_data,
            )
            a_thread.start()
            resp = message(True, "Capture request initiated")
            return resp, 200
        except Exception as error:
            raise
            current_app.logger.error(error)
            return internal_err_resp()

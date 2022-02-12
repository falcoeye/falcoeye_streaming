import json
import threading

import requests
from falcoeye_core.io import source
from flask import current_app
from PIL import Image

from app.utils import internal_err_resp, message


class CaptureService:
    @staticmethod
    def capture_(
        registry_key,
        url,
        stream_provider,
        resolution,
        output_path,
        remote_addr=None,
        remote_port=None,
    ):
        image = source.capture_image(url, stream_provider)
        if image is not None:
            Image.fromarray(image).save(output_path)
            resp = message(True, "Image has been captured.")
            resp["registry_key"] = registry_key
            resp["caputre_status"] = "FAILEDTOCAPUTRE"
        else:
            resp = message(False, "Couldn't capture image. No stream found")
            resp["registry_key"] = registry_key

        if remote_addr:
            postback_url = f"http://{remote_addr}:8000/api/capture/status"
            resp["capture_status"] = "CAPTURED"
            requests.post(postback_url, data=json.dumps(resp))

    @staticmethod
    def capture(
        registry_key,
        url,
        stream_provider,
        resolution,
        output_path,
        remote_addr=None,
        remote_port=None,
    ):
        try:
            a_thread = threading.Thread(
                target=CaptureService.capture_,
                args=[
                    registry_key,
                    url,
                    stream_provider,
                    resolution,
                    output_path,
                    remote_addr,
                    remote_port,
                ],
            )
            a_thread.start()
            resp = message(True, "Capture request initiated")
            return resp, 200
        except Exception as error:
            current_app.logger.error(error)
            return internal_err_resp()

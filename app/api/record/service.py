import json
import threading

import requests
from falcoeye_core.io import source
from flask import current_app
from PIL import Image

from app.utils import internal_err_resp, message


class RecordingService:
    @staticmethod
    def record_(
        registry_key,
        url,
        stream_provider,
        resolution,
        length = -1,
        output_path=None,
        remote_addr=None,
        remote_port=None,
    ):
        recorded = source.record_video(url, stream_provider,resolution,length,output_path)
        if recorded :
            resp = message(True, "Stream has been recorded.")
            resp["registry_key"] = registry_key
            resp["capture_status"] = "RECORDED"
        else:
            resp = message(False, "Couldn't record video. No stream found")
            resp["registry_key"] = registry_key
            resp["caputre_status"] = "FAILEDTORECORD"

        if remote_addr:
            postback_url = f"http://{remote_addr}:8000/api/capture/status"
            requests.post(postback_url, data=json.dumps(resp))

    @staticmethod
    def record(
        registry_key,
        url,
        stream_provider,
        resolution,
        length = -1,
        output_path=None,
        remote_addr=None,
        remote_port=None,
    ):
        try:
            a_thread = threading.Thread(
                target=RecordingService.record_,
                args=[
                    registry_key,
                    url,
                    stream_provider,
                    resolution,
                    length,
                    output_path,
                    remote_addr,
                    remote_port,
                ],
            )
            a_thread.start()
            resp = message(True, "Record request initiated")
            return resp, 200
        except Exception as error:
            current_app.logger.error(error)
            return internal_err_resp()

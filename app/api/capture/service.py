import json
import threading

import requests
from flask import current_app
from PIL import Image

from app.api.core import capture_image, record_video
from app.utils import err_resp, internal_err_resp, message
from .utils import mkdir
import os
import logging
from falcoeye_kubernetes import FalcoServingKube

class CaptureService:
    CAPTURE_REQUESTS = {}
    backend_kube = FalcoServingKube("falcoeye-backend")
    @staticmethod
    def capture_(app, registry_key, camera, output_path, **args):
        logging.info(f"Capturing image for {registry_key} from {camera} and store it in {output_path}")
        image = capture_image(camera)
        if image is not None:
            fdir = os.path.dirname(output_path)
            logging.info(f"Making directory {fdir}")
            mkdir(fdir)
            Image.fromarray(image).save(output_path)
            resp = message(True, "Image has been captured.")
            resp["capture_status"] = "SUCCEEDED"
        else:
            resp = message(False, "Couldn't capture image. No stream found")
            resp["capture_status"] = "FAILED"

        try:
            if app.config["TESTING"]:
                CaptureService.CAPTURE_REQUESTS[registry_key] = resp["capture_status"]

            
            backend_server = CaptureService.backend_kube.get_service_address()
            postback_url = f"http://{backend_server}/api/capture/{registry_key}"
            logging.info(f"Posting new status {resp['capture_status']} to backend {postback_url}")
            rv = requests.post(
                postback_url,
                data=json.dumps(resp),
                headers={"Content-type": "application/json","X-API-KEY":os.environ.get("JWT_KEY")},
            )
            logging.info(f"{rv.json()}")

        except requests.exceptions.ConnectionError:
            logging.error(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
            )
        except requests.exceptions.Timeout:
            logging.error(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
            )
        except requests.exceptions.HTTPError:
            logging.error(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
            )

    @staticmethod
    def record_(app, registry_key, camera, output_path, length=60, **args):
        
        logging.info(f"Recording video with camera {camera} for {length} seconds")
        recorded = record_video(camera, length, output_path)
        logging.info(f"Video recorded? {recorded}")
        if recorded:
            resp = message(True, "Video has been recorded.")
            resp["capture_status"] = "SUCCEEDED"
        else:
            resp = message(False, "Couldn't record video. No stream found")
            resp["capture_status"] = "FAILED"

        if app.config.get("TESTING"):
            CaptureService.CAPTURE_REQUESTS[registry_key] = resp["capture_status"]
        try:
            backend_server = CaptureService.backend_kube.get_service_address()
            postback_url = f"http://{backend_server}/api/capture/status/{registry_key}"
            rv = requests.post(
                postback_url,
                data=json.dumps(resp),
                headers={"Content-type": "application/json","X-API-KEY":os.environ.get("JWT_KEY")},
            )
        except requests.exceptions.ConnectionError:
            print(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
                f"of: {registry_key} due to ConnectionError"
            )
        except requests.exceptions.Timeout:
            print(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
                f"of: {registry_key} due to Timeout"
            )
        except requests.exceptions.HTTPError:
            print(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
                f"of: {registry_key} due to HTTPError"
            )

    @staticmethod
    def capture(data):
        try:
            if data["capture_type"] == "image":
                capture_m = CaptureService.capture_
            else:
                capture_m = CaptureService.record_

            if current_app.config.get("TESTING"):
                CaptureService.CAPTURE_REQUESTS[data["registry_key"]] = "STARTED"
            
            logging.info(f"capture request {data['capture_type']} received with {data}")
            # needed to be able to access app config for testing
            data["app"] = current_app._get_current_object()
            a_thread = threading.Thread(target=capture_m, kwargs=data)
            a_thread.start()
            # capture_m(**data)
            logging.info(f"thread started")
            # Keep reference to check on status without going to backend
            resp = message(True, "Capture request initiated")
            return resp, 200
        except Exception as error:
            logging.error(error)
            current_app.logger.error(error)
            return internal_err_resp()

    @staticmethod
    def get_capture_status(registry_key):
        if registry_key in CaptureService.CAPTURE_REQUESTS:
            resp = message(True, "Capture status sent")
            resp["capture_status"] = CaptureService.CAPTURE_REQUESTS[registry_key]
            return resp
        else:
            return err_resp("Capture not found!", "capture_404", 404)

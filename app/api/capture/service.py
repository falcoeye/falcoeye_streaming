import json
import threading

import requests
from flask import current_app
from PIL import Image

from app.api.core import capture_image, record_video,generate_thumbnail
from app.utils import err_resp, internal_err_resp, message,mkdir,put
import os
import logging
import io
import gcsfs
import numpy as np 
import subprocess


class CaptureService:
    CAPTURE_REQUESTS = {}
    @staticmethod
    def capture_(app, registry_key, camera, output_path, **args):
        logging.info(f"Capturing image for {registry_key} from {camera} and store it in {output_path}")
        image = capture_image(camera)
        #image = np.ones((100,100,3),dtype=np.uint8)
        if image is not None:
            fdir = os.path.dirname(output_path)
            logging.info(f"Making directory {fdir}")
            
            FS_OBJ = app.config["FS_OBJ"]
            mkdir(fdir,app)
            
            
            img = Image.fromarray(image)
            with FS_OBJ.open(os.path.relpath(output_path), "wb") as f:
                byteImgIO = io.BytesIO()
                img.save(byteImgIO, "JPEG")
                byteImgIO.seek(0)
                byteImg = byteImgIO.read()
                f.write(byteImg)
            
            thumbnail_path = f"{os.path.splitext(output_path)[0]}_260.jpg"
            logging.info(f"Creating thumbnail image {thumbnail_path}")
            with FS_OBJ.open(os.path.relpath(thumbnail_path), "wb") as f:
                byteImgIO = io.BytesIO()
                img.thumbnail((260,260))
                logging.info(f"thumbnail size {img.size}")
                img.save(byteImgIO, "JPEG")
                byteImgIO.seek(0)
                byteImg = byteImgIO.read()
                f.write(byteImg)

            resp = message(True, "Image has been captured.")
            resp["capture_status"] = "SUCCEEDED"
        else:
            resp = message(False, "Couldn't capture image. No stream found")
            resp["capture_status"] = "FAILED"

        try:
            if app.config["TESTING"]:
                CaptureService.CAPTURE_REQUESTS[registry_key] = resp["capture_status"]

            
            backend_server = app.config["BACKEND_HOST"]
            postback_url = f"{backend_server}/api/capture/{registry_key}"
            logging.info(f"Posting new status {resp['capture_status']} to backend {postback_url}")
            rv = requests.post(
                postback_url,
                data=json.dumps(resp),
                headers={"Content-type": "application/json","X-API-KEY":os.environ.get("JWT_KEY")},
            )
            if rv.headers["content-type"].strip().startswith("application/json"):
                logging.info(f"Response received {rv.json()}")

            else:
                logging.info(f"Request might have failed. No json response received")

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
        
        if type(length) == str:
            try:
                length = int(length)
            except Exception as e:
                resp = message(False, "Couldn't record video. Length type is wrong")
                resp["capture_status"] = "FAILED"
        logging.info(f"Recording video with camera {camera} for {length} seconds")
        recorded, tmp_path,thumbnail_frame = record_video(camera, length, output_path)
        logging.info(f"Video recorded? {recorded}")
        if recorded:
            fdir = os.path.dirname(output_path)
            logging.info(f"Making directory {fdir}")
            mkdir(fdir,app)

            logging.info(f"Moving recording from {tmp_path} to {output_path}")
            put(tmp_path,output_path,app)
            thumbnail_path = f"{os.path.splitext(output_path)[0]}_260.jpg"
            logging.info(f"Creating thumbnail image {thumbnail_path}")
            FS_OBJ = app.config["FS_OBJ"]
            with FS_OBJ.open(os.path.relpath(thumbnail_path), "wb") as f:
                byteImgIO = io.BytesIO()
                img = Image.fromarray(thumbnail_frame)
                img.thumbnail((260,260))
                img.save(byteImgIO, "JPEG")
                byteImgIO.seek(0)
                byteImg = byteImgIO.read()
                f.write(byteImg)

            logging.info(f"Removing {tmp_path}")
            os.remove(tmp_path)
            resp = message(True, "Video has been recorded.")
            resp["capture_status"] = "SUCCEEDED"
        else:
            resp = message(False, "Couldn't record video. No stream found")
            resp["capture_status"] = "FAILED"

        if app.config.get("TESTING"):
            CaptureService.CAPTURE_REQUESTS[registry_key] = resp["capture_status"]
        
        try:

            backend_server = app.config["BACKEND_HOST"]
            postback_url = f"{backend_server}/api/capture/{registry_key}"
            logging.info(f"Posting new status {resp['capture_status']} to backend {postback_url}")
            rv = requests.post(
                postback_url,
                data=json.dumps(resp),
                headers={"Content-type": "application/json","X-API-KEY":os.environ.get("JWT_KEY")},
            )
            if rv.headers["content-type"].strip().startswith("application/json"):
                logging.info(f"Response received {rv.json()}")
            else:
                logging.warning(f"Request might have failed. No json response received")

        except requests.exceptions.ConnectionError:
            logging.error(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
                f"of: {registry_key} due to ConnectionError"
            )
        except requests.exceptions.Timeout:
            logging.error(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
                f"of: {registry_key} due to Timeout"
            )
        except requests.exceptions.HTTPError:
            logging.error(
                f"Warning: failed to inform backend server ({backend_server}) for change in the status "
                f"of: {registry_key} due to HTTPError"
            )

    @staticmethod
    def generate_thumbnail(app, video_file, output_path, **args):
        FS_OBJ = app.config["FS_OBJ"]
        thumbnail = generate_thumbnail(video_file)
        logging.info(f"Creating thumbnail image {output_path}")
        img = Image.fromarray(thumbnail)
        img.thumbnail((260,260))
        with FS_OBJ.open(os.path.relpath(output_path), "wb") as f:
            byteImgIO = io.BytesIO()
            img.save(byteImgIO, "JPEG")
            byteImgIO.seek(0)
            byteImg = byteImgIO.read()
            f.write(byteImg)

        resp = message(True, "thumbnail created")
        return resp,200

    @staticmethod
    def capture(data):
        try:
            logging.info(data)
            if data["capture_type"] == "image":
                capture_m = CaptureService.capture_
            elif data["capture_type"] == "video":
                capture_m = CaptureService.record_
            elif data["capture_type"] == "thumbnail":
                filename = data.get("video_file")
                output_path = data.get("output_path")
                return CaptureService.generate_thumbnail(current_app._get_current_object(),
                    filename,output_path)

            if current_app.config.get("TESTING"):
                CaptureService.CAPTURE_REQUESTS[data["registry_key"]] = "STARTED"
            
            logging.info(f"capture request {data['capture_type']} received with {data}")
            # needed to be able to access app config for testing
            data["app"] = current_app._get_current_object()
            a_thread = threading.Thread(target=capture_m, kwargs=data)
            a_thread.start()
            #capture_m(**data)
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

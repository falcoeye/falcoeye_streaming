import json
import requests
from app.utils import err_resp, internal_err_resp, message,mkdir,put, get_service
import os
import logging
from app.utils import err_resp, internal_err_resp, message,random_string
from app.k8s.core import FalcoJobKube

class CaptureService:
    @staticmethod
    def capture(data):
        try:
            logging.info(f"New capture requested")
            capture_file = data["capture_file"]
            with open(capture_file) as f:
                data = json.load(f)
            
            if data["type"] == "thumbnail":
                jobname = random_string().lower()
            else:
                jobname = data["registry_key"]

            kube = FalcoJobKube(jobname,capture_file)
            job = kube.start() 
            logging.info(f"Job kube started for {jobname}")
            if job:
                resp = message(True, "capture started")
                return resp, 200
            else:
                resp = err_resp(
                        "Something went wrong. Couldn't start the capture",
                        "capture_403",
                        403,
                    )
                return resp, 403
        except Exception as error:
            logging.error(error)
            return internal_err_resp()

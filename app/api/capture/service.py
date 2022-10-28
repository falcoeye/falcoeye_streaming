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
                # short job, create thumbnail then return
                jobname = random_string().lower()
                kube = FalcoJobKube(jobname,capture_file)
                status = kube.start(watch=True) 
                logging.info(f"Job kube started for thumbnail {jobname}")
                if not status:
                    resp = err_resp("Thumbnail job failed",
                        "capture_403",
                        403,
                    )
                    return resp, 403
                else:
                    resp = message(True, "Thumbnail created")
                    return resp, 200

            else:
                # long job, start and return
                registry_key = data["registry_key"]
                kube = FalcoJobKube(registry_key,capture_file)
                job = kube.start() 
                logging.info(f"Job kube started for {registry_key}")
                if job:
                    resp = message(True, "Capture started")
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

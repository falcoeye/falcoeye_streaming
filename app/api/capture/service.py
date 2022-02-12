import base64

from falcoeye_core.io import source
from flask import current_app

from app.utils import err_resp, internal_err_resp, message

import threading
from PIL import Image


class CaptureService:

    @staticmethod
    def capture_(key,url,stream_provider,resolution,output_path):
        image = source.capture_image(url, stream_provider)
        if image is None:
            resp = message(False, "Couldn't capture image. No stream found")
            resp["registry_key"] = key
            return
        
        Image.fromarray(image).save(output_path)
        resp = message(True, "Image has been captured.")  
        resp["registry_key"] = key
        

    @staticmethod
    def capture(key,url,stream_provider,resolution,output_path):
        try: 
            a_thread = threading.Thread(target=CaptureService.capture_, 
                        args=[key,url,stream_provider,resolution,output_path])
            a_thread.start()  
            resp = message(True, "Capture request initiated")
            return resp, 200
        except Exception as error:
            current_app.logger.error(error)
            return internal_err_resp()

import json

from flask import request
from flask_restx import Namespace, Resource

from app.utils import internal_err_resp

from .service import CaptureService

api = Namespace("capture", description="Capture related operations.")


@api.route("")
class Capture(Resource):


    @api.doc(
        "Get a user media",
        responses={
            200: ("User media successfully sent"),
            404: "User not found!",
        },  # ,security="apikey",
    )
    def post(self):
        """Initiate a caputre request"""
        data = json.loads(request.data.decode("utf-8"))
        return CaptureService.capture(data)

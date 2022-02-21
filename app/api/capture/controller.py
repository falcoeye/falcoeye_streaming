import json

from flask import request
from flask_restx import Namespace, Resource

from app.utils import internal_err_resp

from .service import CaptureService

api = Namespace("capture", description="Capture related operations.")


@api.route("")
class Capture(Resource):
    required_fields = [
        ("registry_key", str),
        ("url", str),
        ("stream_provider", str),
        ("resolution", str),
        ("output_path", str),
    ]

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
        parsed_data = {}
        for field, ftype in Capture.required_fields:
            if field not in data:
                return internal_err_resp()
            parsed_data[field] = ftype(data[field])
        return CaptureService.capture(**parsed_data)

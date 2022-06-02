import json

from flask import request
from flask_restx import Namespace, Resource

from .service import CaptureService

api = Namespace("capture", description="Capture related operations.")


@api.route("")
class Capture(Resource):
    @api.doc(
        "Post capture request",
        responses={
            200: ("Capture request initiated"),
        },
    )
    def post(self):
        """Initiate a caputre request"""
        data = json.loads(request.data.decode("utf-8"))
        return CaptureService.capture(data)


@api.route("/<registry_key>")
class Status(Resource):
    @api.doc("Get a capture status", responses={200: ("Capture status sent")})
    def get(self, registry_key):
        """Initiate a caputre request"""
        return CaptureService.get_capture_status(registry_key)

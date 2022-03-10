import json

from flask import request
from flask_restx import Namespace, Resource

from app.utils import internal_err_resp

from .service import RecordingService

api = Namespace("record", description="Record related operations.")


@api.route("")
class Record(Resource):


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
        # for now these acquired from flask, but
        # should be configurable in future
        return RecordingService.record(data)

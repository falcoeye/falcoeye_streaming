import json

from flask import request
from flask_restx import Namespace, Resource

from app.utils import internal_err_resp

from .service import RecordingService

api = Namespace("record", description="Record related operations.")


@api.route("")
class Record(Resource):
    required_fields = [
        ("registry_key", str),
        ("url", str),
        ("stream_provider", str),
        ("resolution", str),
        ("output_path", str),
    ]
    optional_fields = [
        ("length", int, 60)
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
        # for now these acquired from flask, but
        # should be configurable in future
        host = request.environ["REMOTE_ADDR"]
        port = request.environ["REMOTE_PORT"]
        parsed_data = {}
        for field, ftype in Record.required_fields:
            if field not in data:
                return internal_err_resp()
            parsed_data[field] = ftype(data[field])

        for field, ftype, fdefault in Record.optional_fields:
            if field not in data:
                parsed_data[field] = fdefault
            else:
                parsed_data[field] = ftype(data[field])

        parsed_data["remote_addr"] = host
        parsed_data["remote_port"] = port
        return RecordingService.record(**parsed_data)

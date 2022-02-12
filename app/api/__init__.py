from flask import Blueprint
from flask_restx import Api

from .capture.controller import api as capture_ns

# from .stream.controller import api as stream_ns

authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}}

# Import controller APIs as namespaces.
api_bp = Blueprint("api", __name__)

api = Api(
    api_bp,
    title="API",
    # authorizations=authorizations no auth for now
    description="Main routes.",
)

# API namespaces
api.add_namespace(capture_ns)
# api.add_namespace(stream_ns)

from flask import Blueprint

phl_bp = Blueprint("phl", __name__, url_prefix="/phl")

from app.blueprints.phl import routes  # noqa: E402,F401

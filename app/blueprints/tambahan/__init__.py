from flask import Blueprint

tambahan_bp = Blueprint("tambahan", __name__, url_prefix="/tambahan")

from app.blueprints.tambahan import routes  # noqa: E402,F401

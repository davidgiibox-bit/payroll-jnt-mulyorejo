from flask import Blueprint

master_tunjangan_bp = Blueprint("master_tunjangan", __name__, url_prefix="/master/tunjangan")

from app.blueprints.master_tunjangan import routes  # noqa: E402,F401

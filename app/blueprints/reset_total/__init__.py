from flask import Blueprint

reset_total_bp = Blueprint("reset_total", __name__, url_prefix="/admin/reset-total-database")

from app.blueprints.reset_total import routes  # noqa: E402,F401

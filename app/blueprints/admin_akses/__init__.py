from flask import Blueprint

admin_akses_bp = Blueprint("admin_akses", __name__, url_prefix="/admin/akses")

from app.blueprints.admin_akses import routes  # noqa: E402,F401

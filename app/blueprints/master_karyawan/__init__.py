from flask import Blueprint

master_karyawan_bp = Blueprint("master_karyawan", __name__, url_prefix="/master/karyawan")

from app.blueprints.master_karyawan import routes  # noqa: E402,F401

from flask import Blueprint

master_jabatan_bp = Blueprint("master_jabatan", __name__, url_prefix="/master/jabatan")

from app.blueprints.master_jabatan import routes  # noqa: E402,F401

from flask import Blueprint

potongan_lainnya_bp = Blueprint("potongan_lainnya", __name__, url_prefix="/potongan-lainnya")

from app.blueprints.potongan_lainnya import routes  # noqa: E402,F401

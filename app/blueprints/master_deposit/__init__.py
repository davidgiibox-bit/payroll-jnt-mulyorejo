from flask import Blueprint

master_deposit_bp = Blueprint("master_deposit", __name__, url_prefix="/master/deposit")

from app.blueprints.master_deposit import routes  # noqa: E402,F401

from flask import Blueprint

reward_bp = Blueprint("reward", __name__, url_prefix="/reward")

from app.blueprints.reward import routes  # noqa: E402,F401

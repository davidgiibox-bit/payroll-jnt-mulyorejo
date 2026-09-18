from flask import Blueprint

berita_acara_bp = Blueprint("berita_acara", __name__, url_prefix="/berita-acara")

from app.blueprints.berita_acara import routes  # noqa: E402,F401

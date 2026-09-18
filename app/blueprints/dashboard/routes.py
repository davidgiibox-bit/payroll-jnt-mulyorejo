from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.dashboard import dashboard_bp


@dashboard_bp.route("/")
@login_required
def index():
    return render_template("dashboard/index.html", karyawan=current_user.karyawan)

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Username atau password salah.", "danger")
        elif not user.is_active_account:
            flash("Akun Anda tidak aktif. Hubungi HRD/PIC.", "danger")
        else:
            login_user(user, remember=form.ingat_saya.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            tujuan = request.args.get("next")
            return redirect(tujuan or url_for("dashboard.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))

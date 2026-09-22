from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user, logout_user

from app.blueprints.reset_total import reset_total_bp
from app.blueprints.reset_total.forms import ResetTotalForm
from app.services.reset_service import reset_total_database


@reset_total_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Sengaja TIDAK pakai @butuh_akses (matriks Jabatan x Menu) -- ini di luar sistem
    # hak akses biasa, cuma boleh utk superadmin, dan URL-nya sengaja tidak ada
    # link-nya di navbar mana pun. Dipakai HANYA saat mau tes ulang dari nol.
    if not current_user.is_superadmin:
        abort(403)

    form = ResetTotalForm()
    if form.validate_on_submit():
        pesan_superadmin = reset_total_database()
        logout_user()
        flash(
            "SEMUA data berhasil dihapus & sistem sudah di-seed ulang (menu + superadmin dari env var). "
            f"{pesan_superadmin} Silakan login ulang.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("reset_total/index.html", form=form)

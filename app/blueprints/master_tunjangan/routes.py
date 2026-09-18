from flask import render_template, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models import TunjanganMasaKerjaJenjang
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.master_tunjangan import master_tunjangan_bp
from app.blueprints.master_tunjangan.forms import TunjanganJenjangForm

KODE_MENU = "master_tunjangan"


@master_tunjangan_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_jenjang = TunjanganMasaKerjaJenjang.query.order_by(TunjanganMasaKerjaJenjang.min_bulan).all()
    return render_template("master_tunjangan/index.html", daftar_jenjang=daftar_jenjang)


@master_tunjangan_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def tambah():
    form = TunjanganJenjangForm()
    if form.validate_on_submit():
        jenjang = TunjanganMasaKerjaJenjang()
        form.populate_obj(jenjang)
        db.session.add(jenjang)
        db.session.commit()
        flash("Jenjang tunjangan masa kerja berhasil ditambahkan.", "success")
        return redirect(url_for("master_tunjangan.index"))
    return render_template("master_tunjangan/form.html", form=form, judul="Tambah Jenjang Tunjangan")


@master_tunjangan_bp.route("/<int:jenjang_id>/edit", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def edit(jenjang_id):
    jenjang = TunjanganMasaKerjaJenjang.query.get_or_404(jenjang_id)
    form = TunjanganJenjangForm(obj=jenjang)
    if form.validate_on_submit():
        form.populate_obj(jenjang)
        db.session.commit()
        flash("Jenjang tunjangan masa kerja berhasil diperbarui.", "success")
        return redirect(url_for("master_tunjangan.index"))
    return render_template("master_tunjangan/form.html", form=form, judul="Edit Jenjang Tunjangan")


@master_tunjangan_bp.route("/<int:jenjang_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def hapus(jenjang_id):
    jenjang = TunjanganMasaKerjaJenjang.query.get_or_404(jenjang_id)
    db.session.delete(jenjang)
    db.session.commit()
    flash("Jenjang tunjangan masa kerja berhasil dihapus.", "success")
    return redirect(url_for("master_tunjangan.index"))

from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required

from app.extensions import db
from app.models import Jabatan
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.master_jabatan import master_jabatan_bp
from app.blueprints.master_jabatan.forms import JabatanForm

KODE_MENU = "master_jabatan"


@master_jabatan_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_jabatan = Jabatan.query.order_by(Jabatan.nama).all()
    return render_template("master_jabatan/index.html", daftar_jabatan=daftar_jabatan)


@master_jabatan_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def tambah():
    form = JabatanForm()
    if form.validate_on_submit():
        jabatan = Jabatan(
            nama=form.nama.data.strip(),
            gaji_pokok_default=form.gaji_pokok_default.data,
            kena_phl=form.kena_phl.data,
        )
        db.session.add(jabatan)
        db.session.commit()
        flash(f"Jabatan '{jabatan.nama}' berhasil ditambahkan.", "success")
        return redirect(url_for("master_jabatan.index"))
    return render_template("master_jabatan/form.html", form=form, judul="Tambah Jabatan")


@master_jabatan_bp.route("/<int:jabatan_id>/edit", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def edit(jabatan_id):
    jabatan = Jabatan.query.get_or_404(jabatan_id)
    form = JabatanForm(obj=jabatan)
    if form.validate_on_submit():
        jabatan.nama = form.nama.data.strip()
        jabatan.gaji_pokok_default = form.gaji_pokok_default.data
        jabatan.kena_phl = form.kena_phl.data
        db.session.commit()
        flash(f"Jabatan '{jabatan.nama}' berhasil diperbarui.", "success")
        return redirect(url_for("master_jabatan.index"))
    return render_template("master_jabatan/form.html", form=form, judul="Edit Jabatan")


@master_jabatan_bp.route("/<int:jabatan_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def hapus(jabatan_id):
    jabatan = Jabatan.query.get_or_404(jabatan_id)
    if jabatan.karyawan_list:
        flash(f"Jabatan '{jabatan.nama}' tidak bisa dihapus karena masih dipakai karyawan.", "danger")
        return redirect(url_for("master_jabatan.index"))
    db.session.delete(jabatan)
    db.session.commit()
    flash(f"Jabatan '{jabatan.nama}' berhasil dihapus.", "success")
    return redirect(url_for("master_jabatan.index"))

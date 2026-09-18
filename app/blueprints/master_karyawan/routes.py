from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import Karyawan, Jabatan, DepositSaldo
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.master_karyawan import master_karyawan_bp
from app.blueprints.master_karyawan.forms import KaryawanForm

KODE_MENU = "master_karyawan"


def _isi_pilihan_jabatan(form):
    form.jabatan_id.choices = [(j.id, j.nama) for j in Jabatan.query.order_by(Jabatan.nama).all()]


@master_karyawan_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    kata_kunci = request.args.get("q", "").strip()
    query = Karyawan.query
    if kata_kunci:
        like = f"%{kata_kunci}%"
        query = query.filter(db.or_(Karyawan.nama.ilike(like), Karyawan.nik_karyawan.ilike(like)))
    daftar_karyawan = query.order_by(Karyawan.nama).all()
    return render_template("master_karyawan/index.html", daftar_karyawan=daftar_karyawan, kata_kunci=kata_kunci)


@master_karyawan_bp.route("/<int:karyawan_id>")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def detail(karyawan_id):
    karyawan = Karyawan.query.get_or_404(karyawan_id)
    return render_template("master_karyawan/detail.html", karyawan=karyawan)


@master_karyawan_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def tambah():
    form = KaryawanForm()
    _isi_pilihan_jabatan(form)
    if form.validate_on_submit():
        if Karyawan.query.filter_by(nik_karyawan=form.nik_karyawan.data.strip()).first():
            flash("NIK Karyawan sudah terdaftar.", "danger")
        else:
            karyawan = Karyawan()
            form.populate_obj(karyawan)
            db.session.add(karyawan)
            db.session.flush()
            db.session.add(DepositSaldo(karyawan_id=karyawan.id, saldo_terkumpul=0))
            db.session.commit()
            flash(f"Karyawan '{karyawan.nama}' berhasil ditambahkan.", "success")
            return redirect(url_for("master_karyawan.index"))
    return render_template("master_karyawan/form.html", form=form, judul="Tambah Karyawan")


@master_karyawan_bp.route("/<int:karyawan_id>/edit", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def edit(karyawan_id):
    karyawan = Karyawan.query.get_or_404(karyawan_id)
    form = KaryawanForm(obj=karyawan)
    _isi_pilihan_jabatan(form)
    if form.validate_on_submit():
        nik_baru = form.nik_karyawan.data.strip()
        duplikat = Karyawan.query.filter(
            Karyawan.nik_karyawan == nik_baru, Karyawan.id != karyawan.id
        ).first()
        if duplikat:
            flash("NIK Karyawan sudah dipakai karyawan lain.", "danger")
        else:
            form.populate_obj(karyawan)
            db.session.commit()
            flash(f"Data karyawan '{karyawan.nama}' berhasil diperbarui.", "success")
            return redirect(url_for("master_karyawan.detail", karyawan_id=karyawan.id))
    return render_template("master_karyawan/form.html", form=form, judul="Edit Karyawan", karyawan=karyawan)

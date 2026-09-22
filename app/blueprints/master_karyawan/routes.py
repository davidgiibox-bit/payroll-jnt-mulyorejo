import io

from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
import openpyxl

from app.extensions import db
from app.models import Karyawan, Jabatan, DepositSaldo
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.master_karyawan import master_karyawan_bp
from app.blueprints.master_karyawan.forms import KaryawanForm
from app.services.karyawan_import_service import impor_karyawan

KODE_MENU = "master_karyawan"

KOLOM_TEMPLATE_IMPORT = [
    "Kode DP", "NIK Karyawan", "Nama", "Jabatan", "NPWP", "NIK KTP", "Rekening Bank",
    "Alamat NPWP", "Status Pajak", "Jenis Kelamin", "Tanggal Join", "Tanggal Resign",
    "Status Aktif", "Limit Deposit Individual", "Potongan BPJS-TK", "Tunjangan Masa Kerja",
]


class ImportKaryawanForm(FlaskForm):
    file = FileField(
        "File Template (.xlsx atau .csv)",
        validators=[FileRequired(), FileAllowed(["xlsx", "csv"], "Hanya file .xlsx atau .csv")],
    )
    submit = SubmitField("Import")


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


@master_karyawan_bp.route("/import", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def import_karyawan():
    form = ImportKaryawanForm()
    if form.validate_on_submit():
        laporan = impor_karyawan(form.file.data)
        flash(f"{laporan['baru']} karyawan baru, {laporan['update']} karyawan diperbarui.", "success")
        if laporan["masalah"]:
            flash("Baris dilewati: " + "; ".join(laporan["masalah"]), "warning")
        return redirect(url_for("master_karyawan.index"))
    return render_template("master_karyawan/import.html", form=form)


@master_karyawan_bp.route("/import/template")
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def download_template_import():
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Karyawan"
    sheet.append(KOLOM_TEMPLATE_IMPORT)
    sheet.append([
        "SUB39A", "EMP0001", "Nama Contoh", "Sprinter", "", "", "", "",
        "TK/0", "L", "2024-01-15", "", "Ya", "", "0", "0",
    ])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="template_import_karyawan.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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

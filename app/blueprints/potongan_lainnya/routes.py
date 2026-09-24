from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import PeriodePayroll, JenisPotonganLainnya, PotonganLainnyaEntry, Karyawan
from app.models.periode_payroll import STATUS_FINAL
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.potongan_lainnya import potongan_lainnya_bp
from app.blueprints.potongan_lainnya.forms import JenisPotonganLainnyaForm, UploadPotonganLainnyaForm
from app.services.import_service import parse_template_potongan_lainnya
from app.services.potongan_lainnya_service import hitung_ulang_potongan_lainnya_slip

# Kode menu dipertahankan sama dengan blueprint generik lama ("upload_potongan_lainnya")
# supaya matriks Hak Akses yang sudah dikonfigurasi tim tidak perlu diatur ulang.
KODE_MENU = "upload_potongan_lainnya"


def _daftar_periode():
    return PeriodePayroll.query.order_by(PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()).all()


# --- Master Jenis Potongan Lainnya ---
@potongan_lainnya_bp.route("/jenis")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def jenis_index():
    form = JenisPotonganLainnyaForm()
    daftar_jenis = JenisPotonganLainnya.query.order_by(JenisPotonganLainnya.nama).all()
    return render_template("potongan_lainnya/jenis.html", daftar_jenis=daftar_jenis, form=form)


@potongan_lainnya_bp.route("/jenis/tambah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def jenis_tambah():
    form = JenisPotonganLainnyaForm()
    if form.validate_on_submit():
        if JenisPotonganLainnya.query.filter_by(nama=form.nama.data.strip()).first():
            flash("Jenis potongan lainnya tersebut sudah ada.", "danger")
        else:
            db.session.add(JenisPotonganLainnya(nama=form.nama.data.strip()))
            db.session.commit()
            flash("Jenis potongan lainnya berhasil ditambahkan.", "success")
    return redirect(url_for("potongan_lainnya.jenis_index"))


@potongan_lainnya_bp.route("/jenis/<int:jenis_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def jenis_hapus(jenis_id):
    jenis = JenisPotonganLainnya.query.get_or_404(jenis_id)
    db.session.delete(jenis)
    db.session.commit()
    flash("Jenis potongan lainnya berhasil dihapus.", "success")
    return redirect(url_for("potongan_lainnya.jenis_index"))


# --- Upload Potongan Lainnya ---
@potongan_lainnya_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_periode = _daftar_periode()
    form = UploadPotonganLainnyaForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

    periode_id_dipilih = request.args.get("periode_id", type=int)
    if periode_id_dipilih is None and daftar_periode:
        periode_id_dipilih = daftar_periode[0].id

    daftar_entry = []
    if periode_id_dipilih:
        daftar_entry = (
            PotonganLainnyaEntry.query.filter_by(periode_payroll_id=periode_id_dipilih)
            .join(Karyawan)
            .order_by(Karyawan.nama)
            .all()
        )

    return render_template(
        "potongan_lainnya/index.html",
        form=form,
        daftar_periode=daftar_periode,
        periode_id_dipilih=periode_id_dipilih,
        daftar_entry=daftar_entry,
    )


@potongan_lainnya_bp.route("/template")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def download_template():
    from app.utils.template_excel import kirim_template_excel

    daftar_jenis = [j.nama for j in JenisPotonganLainnya.query.order_by(JenisPotonganLainnya.nama).all()]
    return kirim_template_excel(
        "template_potongan_lainnya.xlsx",
        ["NIK", "Jenis Potongan Lainnya", "Nominal", "Keterangan"],
        ["JM0010001", daftar_jenis[0] if daftar_jenis else "Denda Administrasi", 100000, ""],
        daftar_jenis=daftar_jenis,
        judul_daftar_jenis="Daftar Jenis Potongan Lainnya",
    )


@potongan_lainnya_bp.route("/unggah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def unggah():
    daftar_periode = _daftar_periode()
    form = UploadPotonganLainnyaForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

    if not form.validate_on_submit():
        for field_name, error_list in form.errors.items():
            for error in error_list:
                flash(f"{field_name}: {error}", "danger")
        return redirect(url_for("potongan_lainnya.index"))

    periode = PeriodePayroll.query.get_or_404(form.periode_payroll_id.data)
    if periode.status == STATUS_FINAL:
        flash(f"Periode '{periode.label}' sudah final, potongan lainnya tidak bisa diubah lagi.", "danger")
        return redirect(url_for("potongan_lainnya.index", periode_id=periode.id))

    baris_valid, masalah = parse_template_potongan_lainnya(form.file.data)

    PotonganLainnyaEntry.query.filter_by(periode_payroll_id=periode.id).delete()
    for karyawan, jenis_potongan_lainnya, nominal, keterangan in baris_valid:
        db.session.add(
            PotonganLainnyaEntry(
                periode_payroll_id=periode.id,
                karyawan_id=karyawan.id,
                jenis_potongan_lainnya_id=jenis_potongan_lainnya.id,
                nominal=nominal,
                keterangan=keterangan,
            )
        )
    db.session.flush()
    hitung_ulang_potongan_lainnya_slip(periode)

    flash(f"{len(baris_valid)} baris potongan lainnya berhasil diunggah.", "success")
    if masalah:
        flash("Ada baris yang dilewati: " + "; ".join(masalah), "warning")
    return redirect(url_for("potongan_lainnya.index", periode_id=periode.id))

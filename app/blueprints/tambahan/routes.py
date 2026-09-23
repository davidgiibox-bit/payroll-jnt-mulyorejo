from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import PeriodePayroll, JenisTambahan, TambahanEntry, Karyawan
from app.models.periode_payroll import STATUS_FINAL
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.tambahan import tambahan_bp
from app.blueprints.tambahan.forms import JenisTambahanForm, UploadTambahanForm
from app.services.import_service import parse_template_tambahan
from app.services.tambahan_service import hitung_ulang_tambahan_slip

KODE_MENU = "tambahan"


def _daftar_periode():
    return PeriodePayroll.query.order_by(PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()).all()


# --- Master Jenis Tambahan ---
@tambahan_bp.route("/jenis")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def jenis_index():
    form = JenisTambahanForm()
    daftar_jenis = JenisTambahan.query.order_by(JenisTambahan.nama).all()
    return render_template("tambahan/jenis.html", daftar_jenis=daftar_jenis, form=form)


@tambahan_bp.route("/jenis/tambah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def jenis_tambah():
    form = JenisTambahanForm()
    if form.validate_on_submit():
        if JenisTambahan.query.filter_by(nama=form.nama.data.strip()).first():
            flash("Jenis tambahan tersebut sudah ada.", "danger")
        else:
            db.session.add(JenisTambahan(nama=form.nama.data.strip()))
            db.session.commit()
            flash("Jenis tambahan berhasil ditambahkan.", "success")
    return redirect(url_for("tambahan.jenis_index"))


@tambahan_bp.route("/jenis/<int:jenis_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def jenis_hapus(jenis_id):
    jenis = JenisTambahan.query.get_or_404(jenis_id)
    db.session.delete(jenis)
    db.session.commit()
    flash("Jenis tambahan berhasil dihapus.", "success")
    return redirect(url_for("tambahan.jenis_index"))


# --- Upload Tambahan ---
@tambahan_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_periode = _daftar_periode()
    form = UploadTambahanForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

    periode_id_dipilih = request.args.get("periode_id", type=int)
    if periode_id_dipilih is None and daftar_periode:
        periode_id_dipilih = daftar_periode[0].id

    daftar_entry = []
    if periode_id_dipilih:
        daftar_entry = (
            TambahanEntry.query.filter_by(periode_payroll_id=periode_id_dipilih)
            .join(Karyawan)
            .order_by(Karyawan.nama)
            .all()
        )

    return render_template(
        "tambahan/index.html",
        form=form,
        daftar_periode=daftar_periode,
        periode_id_dipilih=periode_id_dipilih,
        daftar_entry=daftar_entry,
    )


@tambahan_bp.route("/unggah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def unggah():
    daftar_periode = _daftar_periode()
    form = UploadTambahanForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

    if not form.validate_on_submit():
        for field_name, error_list in form.errors.items():
            for error in error_list:
                flash(f"{field_name}: {error}", "danger")
        return redirect(url_for("tambahan.index"))

    periode = PeriodePayroll.query.get_or_404(form.periode_payroll_id.data)
    if periode.status == STATUS_FINAL:
        flash(f"Periode '{periode.label}' sudah final, tambahan tidak bisa diubah lagi.", "danger")
        return redirect(url_for("tambahan.index", periode_id=periode.id))

    baris_valid, masalah = parse_template_tambahan(form.file.data)

    TambahanEntry.query.filter_by(periode_payroll_id=periode.id).delete()
    for karyawan, jenis_tambahan, nominal, keterangan in baris_valid:
        db.session.add(
            TambahanEntry(
                periode_payroll_id=periode.id,
                karyawan_id=karyawan.id,
                jenis_tambahan_id=jenis_tambahan.id,
                nominal=nominal,
                keterangan=keterangan,
            )
        )
    db.session.flush()
    hitung_ulang_tambahan_slip(periode)

    flash(f"{len(baris_valid)} baris tambahan berhasil diunggah.", "success")
    if masalah:
        flash("Ada baris yang dilewati: " + "; ".join(masalah), "warning")
    return redirect(url_for("tambahan.index", periode_id=periode.id))

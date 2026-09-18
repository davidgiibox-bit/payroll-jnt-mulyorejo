from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import PeriodePayroll, PHLPeriode, PHLResiKaryawan, Karyawan
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.phl import phl_bp
from app.blueprints.phl.forms import TotalPHLForm
from app.services.phl_service import hitung_ulang_phl_slip

KODE_MENU = "phl"


@phl_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_periode = PeriodePayroll.query.order_by(
        PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()
    ).all()
    periode_id_dipilih = request.args.get("periode_id", type=int)
    if periode_id_dipilih is None and daftar_periode:
        periode_id_dipilih = daftar_periode[0].id

    phl_periode = None
    daftar_karyawan_phl = []
    peta_resi = {}
    if periode_id_dipilih:
        phl_periode = PHLPeriode.query.filter_by(periode_payroll_id=periode_id_dipilih).first()
        daftar_karyawan_phl = (
            Karyawan.query.join(Karyawan.jabatan)
            .filter(Karyawan.jabatan.has(kena_phl=True), Karyawan.status_aktif.is_(True))
            .order_by(Karyawan.nama)
            .all()
        )
        if phl_periode:
            peta_resi = {r.karyawan_id: r.jumlah_resi for r in phl_periode.resi_list}

    form_total = TotalPHLForm(obj=phl_periode)

    return render_template(
        "phl/index.html",
        daftar_periode=daftar_periode,
        periode_id_dipilih=periode_id_dipilih,
        phl_periode=phl_periode,
        form_total=form_total,
        daftar_karyawan_phl=daftar_karyawan_phl,
        peta_resi=peta_resi,
    )


@phl_bp.route("/<int:periode_id>/simpan-total", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def simpan_total(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    form = TotalPHLForm()
    if not form.validate_on_submit():
        for field_name, error_list in form.errors.items():
            for error in error_list:
                flash(f"{field_name}: {error}", "danger")
        return redirect(url_for("phl.index", periode_id=periode.id))

    phl_periode = PHLPeriode.query.filter_by(periode_payroll_id=periode.id).first()
    if phl_periode is None:
        phl_periode = PHLPeriode(periode_payroll_id=periode.id)
        db.session.add(phl_periode)

    phl_periode.total_biaya = form.total_biaya.data
    phl_periode.total_paket = form.total_paket.data
    db.session.flush()
    hitung_ulang_phl_slip(phl_periode)

    flash("Total biaya PHL berhasil disimpan & potongan dihitung ulang.", "success")
    return redirect(url_for("phl.index", periode_id=periode.id))


@phl_bp.route("/<int:periode_id>/simpan-resi", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def simpan_resi(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    phl_periode = PHLPeriode.query.filter_by(periode_payroll_id=periode.id).first()
    if phl_periode is None:
        flash("Simpan dulu total biaya & total paket sebelum mengisi jumlah resi.", "danger")
        return redirect(url_for("phl.index", periode_id=periode.id))

    daftar_karyawan_phl = (
        Karyawan.query.join(Karyawan.jabatan).filter(Karyawan.jabatan.has(kena_phl=True)).all()
    )
    for karyawan in daftar_karyawan_phl:
        field_name = f"resi_{karyawan.id}"
        nilai = request.form.get(field_name, type=int)
        if nilai is None:
            continue
        resi = PHLResiKaryawan.query.filter_by(
            phl_periode_id=phl_periode.id, karyawan_id=karyawan.id
        ).first()
        if resi is None:
            resi = PHLResiKaryawan(phl_periode_id=phl_periode.id, karyawan_id=karyawan.id)
            db.session.add(resi)
        resi.jumlah_resi = nilai

    db.session.flush()
    hitung_ulang_phl_slip(phl_periode)

    flash("Jumlah resi berhasil disimpan & potongan PHL dihitung ulang.", "success")
    return redirect(url_for("phl.index", periode_id=periode.id))

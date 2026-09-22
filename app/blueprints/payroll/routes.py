from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import PeriodePayroll, SlipGaji, Karyawan
from app.models.periode_payroll import STATUS_FINAL
from app.utils.akses import butuh_akses, punya_akses_minimal
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT, LEVEL_APPROVE
from app.blueprints.payroll import payroll_bp
from app.blueprints.payroll.forms import PeriodePayrollForm, PengaturanSheetForm
from app.services.payroll_engine import proses_periode_payroll
from app.services.google_sheets_client import GoogleSheetsBelumDikonfigurasi
from app.services.kelengkapan_service import ambil_status_kelengkapan
from app.services.periode_service import hapus_periode_payroll, PeriodeTidakBisaDihapus
from app.services.payroll_engine import karyawan_berlaku_pada_periode
from app.services.absensi_manual_service import simpan_absensi_manual
from app.models import AbsensiRingkasanKaryawan

KODE_MENU = "payroll"


@payroll_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_periode = PeriodePayroll.query.order_by(
        PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()
    ).all()
    return render_template("payroll/index.html", daftar_periode=daftar_periode)


@payroll_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def tambah():
    form = PeriodePayrollForm()
    if form.validate_on_submit():
        sudah_ada = PeriodePayroll.query.filter_by(tahun=form.tahun.data, bulan=form.bulan.data).first()
        if sudah_ada:
            flash("Periode tersebut sudah ada.", "danger")
        else:
            periode = PeriodePayroll(tahun=form.tahun.data, bulan=form.bulan.data)
            db.session.add(periode)
            db.session.commit()
            flash(f"Periode '{periode.label}' berhasil dibuat.", "success")
            return redirect(url_for("payroll.detail", periode_id=periode.id))
    return render_template("payroll/form.html", form=form)


@payroll_bp.route("/<int:periode_id>")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def detail(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    daftar_slip = (
        SlipGaji.query.filter_by(periode_payroll_id=periode.id)
        .join(Karyawan)
        .order_by(Karyawan.nama)
        .all()
    )
    status_kelengkapan = ambil_status_kelengkapan(periode)
    return render_template(
        "payroll/detail.html", periode=periode, daftar_slip=daftar_slip, status_kelengkapan=status_kelengkapan
    )


@payroll_bp.route("/<int:periode_id>/pengaturan-sheet", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def pengaturan_sheet(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    form = PengaturanSheetForm(obj=periode)
    if form.validate_on_submit():
        periode.nama_sheet_rekap_override = form.nama_sheet_rekap_override.data.strip() or None
        periode.kode_periode_terlambat_override = form.kode_periode_terlambat_override.data.strip() or None
        db.session.commit()
        flash("Pengaturan sheet berhasil disimpan.", "success")
        return redirect(url_for("payroll.detail", periode_id=periode.id))
    return render_template("payroll/pengaturan_sheet.html", periode=periode, form=form)


@payroll_bp.route("/<int:periode_id>/absensi-manual", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def absensi_manual(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    if periode.status == STATUS_FINAL:
        flash("Periode ini sudah final, absensi tidak bisa diubah lagi.", "danger")
        return redirect(url_for("payroll.detail", periode_id=periode.id))

    daftar_karyawan = [
        k for k in Karyawan.query.order_by(Karyawan.nama).all()
        if karyawan_berlaku_pada_periode(k, periode)
    ]

    if request.method == "POST":
        data_per_karyawan = {}
        for k in daftar_karyawan:
            def ambil(field):
                nilai = request.form.get(f"{field}_{k.id}", "0").strip()
                try:
                    return float(nilai.replace(",", "."))
                except ValueError:
                    return 0

            data_per_karyawan[k.id] = {
                "sakit": ambil("sakit"),
                "izin": ambil("izin"),
                "alpha": ambil("alpha"),
                "tidak_finger": ambil("tidak_finger"),
                "cuti": ambil("cuti"),
                "off": ambil("off"),
                "potongan_terlambat": ambil("terlambat"),
            }

        simpan_absensi_manual(periode, data_per_karyawan)
        flash("Absensi manual berhasil disimpan & slip gaji dihitung ulang memakai data ini.", "success")
        return redirect(url_for("payroll.detail", periode_id=periode.id))

    peta_ringkasan = {
        r.karyawan_id: r
        for r in AbsensiRingkasanKaryawan.query.filter_by(periode_payroll_id=periode.id).all()
    }

    return render_template(
        "payroll/absensi_manual.html",
        periode=periode,
        daftar_karyawan=daftar_karyawan,
        peta_ringkasan=peta_ringkasan,
    )


@payroll_bp.route("/<int:periode_id>/absensi-manual/matikan", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def matikan_absensi_manual(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    periode.absensi_manual = False
    db.session.commit()
    flash("Periode ini kembali memakai Google Sheets. Klik 'Proses / Hitung Ulang' untuk menarik datanya.", "success")
    return redirect(url_for("payroll.detail", periode_id=periode.id))


@payroll_bp.route("/<int:periode_id>/proses", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def proses(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    if periode.status == STATUS_FINAL:
        flash("Periode ini sudah final, tidak bisa diproses ulang.", "danger")
        return redirect(url_for("payroll.detail", periode_id=periode.id))

    try:
        laporan = proses_periode_payroll(periode)
    except GoogleSheetsBelumDikonfigurasi as e:
        flash(str(e), "danger")
        return redirect(url_for("payroll.detail", periode_id=periode.id))

    flash(f"{len(laporan['diproses'])} karyawan berhasil diproses.", "success")
    if laporan["tidak_ditemukan_di_sheet"]:
        nama_list = ", ".join(laporan["tidak_ditemukan_di_sheet"])
        flash(
            f"Nama berikut TIDAK ditemukan di sheet absensi periode ini (dianggap 0 absen/izin, "
            f"mohon cek manual): {nama_list}",
            "warning",
        )
    return redirect(url_for("payroll.detail", periode_id=periode.id))


@payroll_bp.route("/<int:periode_id>/finalisasi", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_APPROVE)
def finalisasi(periode_id):
    from datetime import datetime

    periode = PeriodePayroll.query.get_or_404(periode_id)
    periode.status = STATUS_FINAL
    periode.difinalisasi_at = datetime.utcnow()
    for slip in periode.slip_gaji_list:
        slip.status = STATUS_FINAL
    db.session.commit()
    flash(f"Periode '{periode.label}' berhasil difinalisasi.", "success")
    return redirect(url_for("payroll.detail", periode_id=periode.id))


@payroll_bp.route("/<int:periode_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_APPROVE)
def hapus(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    try:
        label, peringatan = hapus_periode_payroll(periode)
    except PeriodeTidakBisaDihapus as e:
        flash(str(e), "danger")
        return redirect(url_for("payroll.detail", periode_id=periode.id))

    flash(f"Periode '{label}' berhasil dihapus, termasuk membalikkan potongan deposit & cicilan yang sudah terjadi.", "success")
    for pesan in peringatan:
        flash(pesan, "warning")
    return redirect(url_for("payroll.index"))


@payroll_bp.route("/slip/<int:slip_id>")
@login_required
def lihat_slip(slip_id):
    slip = SlipGaji.query.get_or_404(slip_id)
    adalah_milik_sendiri = slip.karyawan_id == current_user.karyawan_id
    if not adalah_milik_sendiri and not punya_akses_minimal(KODE_MENU, LEVEL_LIHAT):
        abort(403)
    return render_template("payroll/slip.html", slip=slip)


@payroll_bp.route("/slip-saya")
@login_required
def slip_saya():
    daftar_slip = (
        SlipGaji.query.filter_by(karyawan_id=current_user.karyawan_id)
        .join(SlipGaji.periode)
        .order_by(PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc())
        .all()
    )
    return render_template("payroll/slip_saya.html", daftar_slip=daftar_slip)

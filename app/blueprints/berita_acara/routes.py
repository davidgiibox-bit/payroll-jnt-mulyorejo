import io

from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required
import openpyxl

from app.extensions import db
from app.models import ReasonClaim, KasusBeritaAcara, Karyawan, PeriodePayroll
from app.models.periode_payroll import STATUS_FINAL
from app.models.berita_acara import STATUS_MENUNGGU_KONFIRMASI, KEPUTUSAN_LANGSUNG, KEPUTUSAN_CICIL
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT, LEVEL_APPROVE
from app.blueprints.berita_acara import berita_acara_bp
from app.blueprints.berita_acara.forms import ReasonClaimForm, UploadFileForm, AssignKasusForm, KeputusanForm
from app.services.berita_acara_service import (
    impor_prediksi,
    impor_pusat,
    buat_cicilan,
    terapkan_potongan_periode,
)

KODE_MENU = "berita_acara"

KOLOM_TEMPLATE_PREDIKSI = ["AWB", "NIK Karyawan", "Nominal", "Reason Claim", "Tanggal", "Keterangan"]
KOLOM_TEMPLATE_PUSAT = [
    "Periode", "Tahun", "Jenis Ecommerce", "AWB", "Lokasi Tertagih", "Nilai Claim",
    "Mitra", "Region", "RM", "Status Bayar", "Keterangan", "Reason Claim",
]


def _buat_file_template(kolom, contoh_baris):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Template"
    sheet.append(kolom)
    sheet.append(contoh_baris)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


# --- Master Reason Claim ---
@berita_acara_bp.route("/reason")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def reason_index():
    daftar = ReasonClaim.query.order_by(ReasonClaim.nama).all()
    return render_template("berita_acara/reason.html", daftar=daftar, form=ReasonClaimForm())


@berita_acara_bp.route("/reason/tambah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def reason_tambah():
    form = ReasonClaimForm()
    if form.validate_on_submit():
        if ReasonClaim.query.filter_by(nama=form.nama.data.strip()).first():
            flash("Reason claim tersebut sudah ada.", "danger")
        else:
            db.session.add(ReasonClaim(nama=form.nama.data.strip()))
            db.session.commit()
            flash("Reason claim berhasil ditambahkan.", "success")
    return redirect(url_for("berita_acara.reason_index"))


@berita_acara_bp.route("/reason/<int:reason_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def reason_hapus(reason_id):
    reason = ReasonClaim.query.get_or_404(reason_id)
    db.session.delete(reason)
    db.session.commit()
    flash("Reason claim berhasil dihapus.", "success")
    return redirect(url_for("berita_acara.reason_index"))


# --- Daftar Kasus ---
@berita_acara_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    status_filter = request.args.get("status", "")
    query = KasusBeritaAcara.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    daftar_kasus = query.order_by(KasusBeritaAcara.created_at.desc()).limit(200).all()
    return render_template("berita_acara/index.html", daftar_kasus=daftar_kasus, status_filter=status_filter)


# --- Upload Template Prediksi ---
@berita_acara_bp.route("/upload-prediksi", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def upload_prediksi():
    form = UploadFileForm()
    if form.validate_on_submit():
        laporan = impor_prediksi(form.file.data)
        flash(f"{laporan['baru']} kasus baru, {laporan['update']} kasus diperbarui.", "success")
        if laporan["masalah"]:
            flash("Baris dilewati: " + "; ".join(laporan["masalah"]), "warning")
        return redirect(url_for("berita_acara.index"))
    return render_template(
        "berita_acara/upload.html",
        form=form,
        judul="Upload Template Prediksi (Tim)",
        keterangan_format="Kolom: AWB, NIK Karyawan, Nominal, Reason Claim, Tanggal, Keterangan.",
        url_template="berita_acara.download_template_prediksi",
    )


# --- Upload Template Pusat ---
@berita_acara_bp.route("/upload-pusat", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def upload_pusat():
    form = UploadFileForm()
    if form.validate_on_submit():
        laporan = impor_pusat(form.file.data)
        flash(
            f"{laporan['baru']} kasus baru (butuh assignment manual), "
            f"{laporan['cocok']} kasus cocok & final, {laporan['selisih']} kasus ada selisih nominal.",
            "success",
        )
        if laporan["masalah"]:
            flash("Catatan: " + "; ".join(laporan["masalah"]), "warning")
        return redirect(url_for("berita_acara.index"))
    return render_template(
        "berita_acara/upload.html",
        form=form,
        judul="Upload Template Pusat (Konfirmasi HQ)",
        keterangan_format="Kolom: Periode, Tahun, Jenis Ecommerce, AWB, Lokasi Tertagih, Nilai Claim, Mitra, Region, RM, Status Bayar, Keterangan, Reason Claim.",
        url_template="berita_acara.download_template_pusat",
    )


@berita_acara_bp.route("/upload-prediksi/template")
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def download_template_prediksi():
    contoh = ["JX1234567890", "JM0010001", "150000", "Salah Alamat", "2026-09-15", "Paket rusak"]
    buffer = _buat_file_template(KOLOM_TEMPLATE_PREDIKSI, contoh)
    return send_file(
        buffer, as_attachment=True, download_name="template_prediksi_berita_acara.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@berita_acara_bp.route("/upload-pusat/template")
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def download_template_pusat():
    contoh = [
        "September", "2026", "Shopee", "JX1234567890", "MULYOREJO", "150000",
        "AGENT19", "JBR-PROBOLINGGO", "RM Contoh", "Belum Bayar", "Catatan", "Salah Alamat",
    ]
    buffer = _buat_file_template(KOLOM_TEMPLATE_PUSAT, contoh)
    return send_file(
        buffer, as_attachment=True, download_name="template_pusat_berita_acara.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --- Assignment Manual (kasus dari pusat, belum ada karyawan) ---
@berita_acara_bp.route("/assign")
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def assign_index():
    daftar = KasusBeritaAcara.query.filter_by(karyawan_id=None).order_by(KasusBeritaAcara.created_at.desc()).all()
    return render_template("berita_acara/assign_index.html", daftar=daftar)


@berita_acara_bp.route("/assign/<int:kasus_id>", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def assign_kasus(kasus_id):
    kasus = KasusBeritaAcara.query.get_or_404(kasus_id)
    form = AssignKasusForm()
    form.karyawan_id.choices = [(k.id, f"{k.nik_karyawan} - {k.nama}") for k in Karyawan.query.order_by(Karyawan.nama).all()]
    form.reason_claim_id.choices = [(r.id, r.nama) for r in ReasonClaim.query.order_by(ReasonClaim.nama).all()]

    if form.validate_on_submit():
        kasus.karyawan_id = form.karyawan_id.data
        kasus.reason_claim_id = form.reason_claim_id.data
        kasus.nominal_final = kasus.nominal_pusat
        kasus.keputusan = KEPUTUSAN_LANGSUNG
        db.session.commit()
        flash(f"Kasus AWB {kasus.awb} berhasil di-assign.", "success")
        return redirect(url_for("berita_acara.assign_index"))

    return render_template("berita_acara/assign_form.html", kasus=kasus, form=form)


# --- Ubah Keputusan (langsung / cicil) ---
@berita_acara_bp.route("/kasus/<int:kasus_id>/keputusan", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def ubah_keputusan(kasus_id):
    kasus = KasusBeritaAcara.query.get_or_404(kasus_id)
    if kasus.sudah_diterapkan:
        flash("Kasus ini sudah pernah diterapkan ke suatu periode, keputusan tidak bisa diubah lagi.", "danger")
        return redirect(url_for("berita_acara.index"))

    form = KeputusanForm(keputusan=kasus.keputusan or KEPUTUSAN_LANGSUNG, jumlah_bulan=kasus.jumlah_bulan_cicilan or 3)
    if form.validate_on_submit():
        if form.keputusan.data == KEPUTUSAN_CICIL:
            buat_cicilan(kasus, form.jumlah_bulan.data)
        else:
            if kasus.cicilan:
                db.session.delete(kasus.cicilan)
            kasus.keputusan = KEPUTUSAN_LANGSUNG
            kasus.jumlah_bulan_cicilan = None
            db.session.commit()
        flash("Keputusan berhasil disimpan.", "success")
        return redirect(url_for("berita_acara.review"))
    return render_template("berita_acara/keputusan_form.html", kasus=kasus, form=form)


# --- Review Sebelum Final (poin l) ---
@berita_acara_bp.route("/review")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def review():
    daftar_periode = PeriodePayroll.query.order_by(PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()).all()
    periode_id_dipilih = request.args.get("periode_id", type=int)
    if periode_id_dipilih is None and daftar_periode:
        periode_id_dipilih = daftar_periode[0].id

    daftar_kasus = (
        KasusBeritaAcara.query.filter(KasusBeritaAcara.karyawan_id.isnot(None))
        .order_by(KasusBeritaAcara.nominal_final.desc())
        .all()
    )

    per_karyawan = {}
    for kasus in daftar_kasus:
        if kasus.sudah_diterapkan and not (kasus.cicilan and kasus.cicilan.status == "aktif"):
            continue
        nama = kasus.karyawan.nama
        per_karyawan.setdefault(nama, {"kasus": [], "total": 0})
        per_karyawan[nama]["kasus"].append(kasus)
        per_karyawan[nama]["total"] += float(kasus.nominal_final or 0)

    daftar_terurut = sorted(per_karyawan.items(), key=lambda x: x[1]["total"], reverse=True)

    return render_template(
        "berita_acara/review.html",
        daftar_periode=daftar_periode,
        periode_id_dipilih=periode_id_dipilih,
        daftar_terurut=daftar_terurut,
    )


@berita_acara_bp.route("/terapkan/<int:periode_id>", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_APPROVE)
def terapkan(periode_id):
    periode = PeriodePayroll.query.get_or_404(periode_id)
    if periode.status == STATUS_FINAL:
        flash(f"Periode '{periode.label}' sudah final, potongan Berita Acara tidak bisa diubah lagi.", "danger")
        return redirect(url_for("berita_acara.review", periode_id=periode.id))

    laporan = terapkan_potongan_periode(periode)
    flash(f"Potongan Berita Acara/Cicilan berhasil diterapkan ke periode {periode.label}.", "success")
    for peringatan in laporan["peringatan"]:
        flash(peringatan, "warning")
    return redirect(url_for("berita_acara.review", periode_id=periode.id))

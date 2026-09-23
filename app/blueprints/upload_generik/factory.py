from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import PeriodePayroll, KomponenUpload, Karyawan
from app.models.periode_payroll import STATUS_FINAL
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.upload_generik.forms import UploadKomponenForm
from app.services.komponen_upload_service import unggah_komponen


def buat_blueprint_upload(slug, kode_menu, label, jenis, arah):
    """Bikin 1 blueprint upload komponen generik (NIK + nominal + keterangan).

    slug: dipakai untuk nama blueprint & url prefix, mis. 'bbm'.
    kode_menu: kode menu untuk hak akses (matriks Jabatan x Menu), terpisah per komponen.
    label: nama tampilan, mis. 'Potongan BBM'.
    jenis: salah satu konstanta JENIS_* di app.models.komponen_upload.
    arah: 'tambah' atau 'potongan', hanya untuk label tampilan.
    """
    bp = Blueprint(f"upload_{slug}", __name__, url_prefix=f"/upload/{slug}")

    @bp.route("/", endpoint="index")
    @login_required
    @butuh_akses(kode_menu, LEVEL_LIHAT)
    def index():
        daftar_periode = PeriodePayroll.query.order_by(
            PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()
        ).all()

        form = UploadKomponenForm()
        form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

        periode_id_dipilih = request.args.get("periode_id", type=int)
        if periode_id_dipilih is None and daftar_periode:
            periode_id_dipilih = daftar_periode[0].id

        daftar_baris = []
        if periode_id_dipilih:
            daftar_baris = (
                KomponenUpload.query.filter_by(periode_payroll_id=periode_id_dipilih, jenis=jenis)
                .join(Karyawan)
                .order_by(Karyawan.nama)
                .all()
            )

        return render_template(
            "upload_generik/index.html",
            label=label,
            arah=arah,
            form=form,
            daftar_periode=daftar_periode,
            periode_id_dipilih=periode_id_dipilih,
            daftar_baris=daftar_baris,
            kode_menu=kode_menu,
        )

    @bp.route("/unggah", methods=["POST"], endpoint="unggah")
    @login_required
    @butuh_akses(kode_menu, LEVEL_EDIT)
    def unggah():
        daftar_periode = PeriodePayroll.query.order_by(
            PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()
        ).all()
        form = UploadKomponenForm()
        form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

        if not form.validate_on_submit():
            for field_name, error_list in form.errors.items():
                for error in error_list:
                    flash(f"{field_name}: {error}", "danger")
            return redirect(url_for(f"upload_{slug}.index"))

        periode = PeriodePayroll.query.get_or_404(form.periode_payroll_id.data)
        if periode.status == STATUS_FINAL:
            flash(f"Periode '{periode.label}' sudah final, {label} tidak bisa diubah lagi.", "danger")
            return redirect(url_for(f"upload_{slug}.index", periode_id=periode.id))

        laporan = unggah_komponen(periode, jenis, form.file.data, current_user.id)

        flash(f"{laporan['jumlah_baris']} baris {label} berhasil diunggah untuk periode {periode.label}.", "success")
        if laporan["nik_tidak_ditemukan"]:
            flash(
                "NIK berikut tidak ditemukan dan dilewati: " + ", ".join(laporan["nik_tidak_ditemukan"]),
                "warning",
            )
        return redirect(url_for(f"upload_{slug}.index", periode_id=periode.id))

    return bp

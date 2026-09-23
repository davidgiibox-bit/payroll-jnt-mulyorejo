from decimal import Decimal

from app.extensions import db
from app.models import AbsensiRingkasanKaryawan
from app.services.payroll_engine import proses_periode_payroll


def simpan_absensi_manual(periode, data_per_karyawan):
    """data_per_karyawan: dict {karyawan_id: {sakit, izin, alpha, tidak_finger, cuti,
    off, potongan_terlambat}}. Alpha+Tdk Finger dihitung otomatis (alpha + tidak_finger),
    sama seperti kolom gabungan di sheet Google Sheets asli.

    Menandai periode.absensi_manual = True lalu memicu hitung ulang slip (proses_periode_payroll)
    memakai data ini sebagai sumber, TANPA menarik Google Sheets."""
    for karyawan_id, data in data_per_karyawan.items():
        ringkasan = AbsensiRingkasanKaryawan.query.filter_by(
            periode_payroll_id=periode.id, karyawan_id=karyawan_id
        ).first()
        if ringkasan is None:
            ringkasan = AbsensiRingkasanKaryawan(periode_payroll_id=periode.id, karyawan_id=karyawan_id)
            db.session.add(ringkasan)

        ringkasan.sakit = Decimal(str(data["sakit"]))
        ringkasan.izin = Decimal(str(data["izin"]))
        ringkasan.alpha = Decimal(str(data["alpha"]))
        ringkasan.tidak_finger = Decimal(str(data["tidak_finger"]))
        ringkasan.alpha_tdk_finger = ringkasan.alpha + ringkasan.tidak_finger
        ringkasan.cuti = Decimal(str(data["cuti"]))
        ringkasan.off = Decimal(str(data["off"]))
        ringkasan.total_hari = Decimal(str(data["total_hari"]))
        ringkasan.potongan_terlambat = Decimal(str(data["potongan_terlambat"]))

    periode.absensi_manual = True
    db.session.commit()

    proses_periode_payroll(periode)

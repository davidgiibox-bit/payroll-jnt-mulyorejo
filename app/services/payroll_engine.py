from calendar import monthrange
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import (
    Karyawan,
    DepositSaldo,
    DepositTransaksi,
    PengaturanDeposit,
    AbsensiRingkasanKaryawan,
    SlipGaji,
)
from app.services.absensi_service import ambil_rekap_absensi_periode, ambil_potongan_terlambat_periode


def _rentang_periode(periode_payroll):
    awal = date(periode_payroll.tahun, periode_payroll.bulan, 1)
    akhir_hari = monthrange(periode_payroll.tahun, periode_payroll.bulan)[1]
    akhir = date(periode_payroll.tahun, periode_payroll.bulan, akhir_hari)
    return awal, akhir


def karyawan_berlaku_pada_periode(karyawan, periode_payroll):
    awal, akhir = _rentang_periode(periode_payroll)
    if karyawan.tanggal_join and karyawan.tanggal_join > akhir:
        return False
    if karyawan.tanggal_resign and karyawan.tanggal_resign < awal:
        return False
    return True


def hitung_potongan_kehadiran(gaji_pokok, tunjangan, alpha_tdk_finger, izin):
    """Potongan Kehadiran = (GajiPokok + Tunjangan) / 25 x (Alpha+TdkFinger + Izin).
    Sakit, Cuti, Off/Dinas TIDAK dipotong."""
    dasar = (Decimal(gaji_pokok) + Decimal(tunjangan)) / Decimal(25)
    return dasar * Decimal(str(alpha_tdk_finger + izin))


def proses_potongan_deposit(karyawan, periode_payroll):
    """Terapkan potongan deposit bulanan, hormati limit & saldo berjalan.
    Berhenti motong kalau limit sudah tercapai. Mengembalikan nominal potongan aktual."""
    deposit_saldo = DepositSaldo.query.filter_by(karyawan_id=karyawan.id).first()
    if deposit_saldo is None:
        deposit_saldo = DepositSaldo(karyawan_id=karyawan.id, saldo_terkumpul=0)
        db.session.add(deposit_saldo)
        db.session.flush()

    sudah_ada_transaksi = any(
        t.periode == f"{periode_payroll.tahun:04d}-{periode_payroll.bulan:02d}" and t.jenis == "otomatis"
        for t in deposit_saldo.transaksi_list
    )
    if sudah_ada_transaksi:
        return Decimal("0")  # potongan periode ini sudah pernah diproses sebelumnya

    limit_efektif = Decimal(deposit_saldo.limit_efektif())
    sisa_ruang = limit_efektif - Decimal(deposit_saldo.saldo_terkumpul)
    if sisa_ruang <= 0:
        return Decimal("0")

    default_potongan = PengaturanDeposit.get_current().default_potongan_bulanan
    potongan = min(Decimal(default_potongan), sisa_ruang)

    deposit_saldo.saldo_terkumpul = Decimal(deposit_saldo.saldo_terkumpul) + potongan
    db.session.add(
        DepositTransaksi(
            deposit_saldo_id=deposit_saldo.id,
            periode=f"{periode_payroll.tahun:04d}-{periode_payroll.bulan:02d}",
            jenis="otomatis",
            nominal=potongan,
            saldo_setelah=deposit_saldo.saldo_terkumpul,
        )
    )
    return potongan


def proses_periode_payroll(periode_payroll):
    """Proses inti Fase 2: tarik absensi dari Google Sheets, hitung potongan kehadiran,
    potongan terlambat, potongan deposit, snapshot gaji pokok & tunjangan, lalu simpan
    sebagai SlipGaji berstatus draft untuk semua karyawan yang berlaku pada periode ini.

    Mengembalikan dict laporan: {'diproses': [...nama...], 'tidak_ditemukan_di_sheet': [...]}.
    """
    rekap_absensi = ambil_rekap_absensi_periode(periode_payroll)
    potongan_terlambat_map = ambil_potongan_terlambat_periode(periode_payroll)

    daftar_karyawan = Karyawan.query.all()
    diproses = []
    tidak_ditemukan_di_sheet = []

    for karyawan in daftar_karyawan:
        if not karyawan_berlaku_pada_periode(karyawan, periode_payroll):
            continue

        kunci_nama = karyawan.nama.strip().lower()
        data_absensi = rekap_absensi.get(kunci_nama)
        if data_absensi is None:
            tidak_ditemukan_di_sheet.append(karyawan.nama)
            data_absensi = {"sakit": 0, "izin": 0, "alpha": 0, "tidak_finger": 0, "alpha_tdk_finger": 0, "cuti": 0, "off": 0}

        AbsensiRingkasanKaryawan.query.filter_by(
            periode_payroll_id=periode_payroll.id, karyawan_id=karyawan.id
        ).delete()
        potongan_terlambat = Decimal(str(potongan_terlambat_map.get(kunci_nama, 0)))
        ringkasan = AbsensiRingkasanKaryawan(
            periode_payroll_id=periode_payroll.id,
            karyawan_id=karyawan.id,
            sakit=data_absensi["sakit"],
            izin=data_absensi["izin"],
            alpha=data_absensi["alpha"],
            tidak_finger=data_absensi["tidak_finger"],
            alpha_tdk_finger=data_absensi["alpha_tdk_finger"],
            cuti=data_absensi["cuti"],
            off=data_absensi["off"],
            potongan_terlambat=potongan_terlambat,
        )
        db.session.add(ringkasan)

        gaji_pokok = karyawan.jabatan.gaji_pokok_default
        tunjangan = karyawan.tunjangan_masa_kerja
        potongan_kehadiran = hitung_potongan_kehadiran(
            gaji_pokok, tunjangan, data_absensi["alpha_tdk_finger"], data_absensi["izin"]
        )
        potongan_deposit = proses_potongan_deposit(karyawan, periode_payroll)

        slip = SlipGaji.query.filter_by(
            periode_payroll_id=periode_payroll.id, karyawan_id=karyawan.id
        ).first()
        if slip is None:
            slip = SlipGaji(periode_payroll_id=periode_payroll.id, karyawan_id=karyawan.id)
            db.session.add(slip)

        slip.gaji_pokok_snapshot = gaji_pokok
        slip.tunjangan_masa_kerja_snapshot = tunjangan
        slip.potongan_kehadiran = potongan_kehadiran
        slip.potongan_terlambat = potongan_terlambat
        slip.potongan_deposit = potongan_deposit
        slip.potongan_bpjs_tk = karyawan.potongan_bpjs_tk
        slip.hitung_ulang()

        diproses.append(karyawan.nama)

    db.session.commit()
    return {"diproses": diproses, "tidak_ditemukan_di_sheet": tidak_ditemukan_di_sheet}

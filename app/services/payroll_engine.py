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
    if not karyawan.status_aktif and not (karyawan.tanggal_resign and awal <= karyawan.tanggal_resign <= akhir):
        # status_aktif dimatikan (tanpa tanggal resign yang jatuh di periode ini) —
        # konsisten dengan badge Aktif/Tidak Aktif, jangan ikut diproses payroll.
        return False
    return True


def hitung_potongan_kehadiran(gaji_pokok, tunjangan, total_hari, sakit, cuti):
    """Potongan Kehadiran = ((GajiPokok+Tunjangan)/25 x (TotalHari+Sakit+Cuti)) - (GajiPokok+Tunjangan).
    Total Hari ditarik apa adanya dari sumber data (tim absensi sudah menghitung &
    membatasinya, mis. maksimal 25 untuk periode penuh) - divisor SELALU tetap 25,
    tidak diprorata. Sakit & Cuti dianggap tetap dibayar sehingga ditambahkan lagi
    di sisi kiri supaya tidak ikut memotong."""
    gapok_tunjangan = Decimal(gaji_pokok) + Decimal(tunjangan)
    dasar = gapok_tunjangan / Decimal(25)
    hari_dibayar = Decimal(str(total_hari)) + Decimal(str(sakit)) + Decimal(str(cuti))
    return gapok_tunjangan - (dasar * hari_dibayar)


def proses_potongan_deposit(karyawan, periode_payroll):
    """Terapkan potongan deposit bulanan, hormati limit & saldo berjalan.
    Berhenti motong kalau limit sudah tercapai. Mengembalikan nominal potongan aktual."""
    deposit_saldo = DepositSaldo.query.filter_by(karyawan_id=karyawan.id).first()
    if deposit_saldo is None:
        deposit_saldo = DepositSaldo(karyawan_id=karyawan.id, saldo_terkumpul=0)
        db.session.add(deposit_saldo)
        db.session.flush()

    kode_periode = f"{periode_payroll.tahun:04d}-{periode_payroll.bulan:02d}"
    transaksi_sebelumnya = next(
        (t for t in deposit_saldo.transaksi_list if t.periode == kode_periode and t.jenis == "otomatis"),
        None,
    )
    limit_efektif = Decimal(deposit_saldo.limit_efektif())

    if transaksi_sebelumnya is not None:
        if limit_efektif <= 0:
            # Limit karyawan ini SEKARANG 0 (tidak boleh dipotong sama sekali) — batalkan
            # potongan periode ini yang sempat tercatat sebelum limit diubah, supaya
            # proses ulang selalu ikut aturan terkini, bukan angka basi dari histori lama.
            deposit_saldo.saldo_terkumpul = Decimal(deposit_saldo.saldo_terkumpul) - Decimal(transaksi_sebelumnya.nominal)
            db.session.delete(transaksi_sebelumnya)
            return Decimal("0")
        # Sudah pernah diproses periode ini & limit masih berlaku — kembalikan nominal
        # yang sama (bukan 0), supaya diproses ulang tidak membuat potongan_deposit di
        # slip jadi hilang, dan tidak memotong dobel.
        return Decimal(transaksi_sebelumnya.nominal)

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


def _rekap_absensi_dari_data_manual(periode_payroll):
    """Bangun ulang rekap_absensi & potongan_terlambat_map dari AbsensiRingkasanKaryawan
    yang sudah tersimpan (diisi manual), dipakai kalau periode.absensi_manual = True
    supaya proses_periode_payroll TIDAK menarik/menimpa dengan data Google Sheets."""
    rekap_absensi = {}
    potongan_terlambat_map = {}
    for ringkasan in periode_payroll.absensi_ringkasan_list:
        kunci = ringkasan.karyawan.nama.strip().lower()
        rekap_absensi[kunci] = {
            "sakit": float(ringkasan.sakit),
            "izin": float(ringkasan.izin),
            "alpha": float(ringkasan.alpha),
            "tidak_finger": float(ringkasan.tidak_finger),
            "alpha_tdk_finger": float(ringkasan.alpha_tdk_finger),
            "cuti": float(ringkasan.cuti),
            "off": float(ringkasan.off),
            "dinas": float(ringkasan.dinas),
            "total_hari": float(ringkasan.total_hari),
        }
        potongan_terlambat_map[kunci] = float(ringkasan.potongan_terlambat)
    return rekap_absensi, potongan_terlambat_map


def proses_periode_payroll(periode_payroll):
    """Proses inti Fase 2: tarik absensi dari Google Sheets (atau pakai data manual kalau
    periode_payroll.absensi_manual = True), hitung potongan kehadiran, potongan terlambat,
    potongan deposit, snapshot gaji pokok & tunjangan, lalu simpan sebagai SlipGaji
    berstatus draft untuk semua karyawan yang berlaku pada periode ini.

    Mengembalikan dict laporan: {'diproses': [...nama...], 'tidak_ditemukan_di_sheet': [...]}.
    """
    if periode_payroll.absensi_manual:
        rekap_absensi, potongan_terlambat_map = _rekap_absensi_dari_data_manual(periode_payroll)
    else:
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
            if not periode_payroll.absensi_manual:
                tidak_ditemukan_di_sheet.append(karyawan.nama)
            data_absensi = {
                "sakit": 0, "izin": 0, "alpha": 0, "tidak_finger": 0, "alpha_tdk_finger": 0,
                "cuti": 0, "off": 0, "dinas": 0, "total_hari": 0,
            }

        potongan_terlambat = Decimal(str(potongan_terlambat_map.get(kunci_nama, 0)))

        if not periode_payroll.absensi_manual:
            # Mode Google Sheets: hapus & tulis ulang ringkasan tiap proses.
            # Mode manual: JANGAN dihapus/ditimpa di sini — datanya sudah disimpan
            # apa adanya oleh halaman Input Absensi Manual.
            AbsensiRingkasanKaryawan.query.filter_by(
                periode_payroll_id=periode_payroll.id, karyawan_id=karyawan.id
            ).delete()
            db.session.add(
                AbsensiRingkasanKaryawan(
                    periode_payroll_id=periode_payroll.id,
                    karyawan_id=karyawan.id,
                    sakit=data_absensi["sakit"],
                    izin=data_absensi["izin"],
                    alpha=data_absensi["alpha"],
                    tidak_finger=data_absensi["tidak_finger"],
                    alpha_tdk_finger=data_absensi["alpha_tdk_finger"],
                    cuti=data_absensi["cuti"],
                    off=data_absensi["off"],
                    dinas=data_absensi["dinas"],
                    total_hari=data_absensi["total_hari"],
                    potongan_terlambat=potongan_terlambat,
                )
            )

        gaji_pokok = karyawan.jabatan.gaji_pokok_default
        tunjangan = karyawan.tunjangan_masa_kerja
        potongan_kehadiran = hitung_potongan_kehadiran(
            gaji_pokok, tunjangan, data_absensi["total_hari"], data_absensi["sakit"], data_absensi["cuti"]
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

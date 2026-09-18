import gspread

from app.services.google_sheets_client import buka_spreadsheet_absensi, ambil_semua_baris

NAMA_SHEET_KETERLAMBATAN = "KeterlambatanLog"


def _normalisasi_nama(nama):
    return (nama or "").strip().lower()


def _ke_angka(nilai):
    if nilai in (None, ""):
        return 0
    try:
        return float(str(nilai).replace(",", "."))
    except ValueError:
        return 0


def _cari_baris_header(all_values):
    """Sheet 'Rekap [Bulan] [Tahun]' punya header 2-baris (baris 1 kosong/judul,
    header sebenarnya di baris berikutnya, kolom Masuk/Keluar per tanggal di
    bawahnya lagi) — cari baris yang kolom pertamanya persis 'DP'."""
    for i, row in enumerate(all_values):
        if row and row[0].strip().upper() == "DP":
            return i
    return None


def _cari_kolom(header_row, *nama_alternatif):
    for nama in nama_alternatif:
        if nama in header_row:
            return header_row.index(nama)
    return None


def _ambil(row, idx):
    if idx is None or idx >= len(row):
        return ""
    return row[idx]


def ambil_rekap_absensi_periode(periode_payroll):
    """Tarik sheet 'Rekap {Bulan} {Tahun}' dan kembalikan dict {nama_normalisasi: data}.

    Sheet ini punya header majemuk (kolom Masuk/Keluar per tanggal berubah-ubah jumlah
    kolomnya tiap bulan) sehingga tidak bisa dibaca dengan get_all_records biasa — kolom
    dicari berdasarkan nama header, posisinya fleksibel.

    Mengembalikan dict kosong kalau sheet untuk periode tsb belum ada (mis. bulan baru
    yang sheetnya belum dibuat tim) — pemanggil sebaiknya menampilkan peringatan ke user.
    """
    spreadsheet = buka_spreadsheet_absensi()
    nama_sheet = periode_payroll.nama_sheet_rekap

    try:
        worksheet = spreadsheet.worksheet(nama_sheet)
    except gspread.exceptions.WorksheetNotFound:
        return {}

    all_values = worksheet.get_all_values()
    idx_header = _cari_baris_header(all_values)
    if idx_header is None:
        return {}

    header_row = all_values[idx_header]
    kolom = {
        "dp": _cari_kolom(header_row, "DP"),
        "nama": _cari_kolom(header_row, "NAMA KARYAWAN", "Nama Karyawan", "Nama"),
        "jabatan": _cari_kolom(header_row, "JABATAN", "Jabatan"),
        "sakit": _cari_kolom(header_row, "Sakit"),
        "izin": _cari_kolom(header_row, "Izin"),
        "alpha": _cari_kolom(header_row, "Alpha"),
        "tidak_finger": _cari_kolom(header_row, "Tidak Finger"),
        "alpha_tdk_finger": _cari_kolom(header_row, "Total Alpha + Tdk Finger", "Alpha + Tdk Finger"),
        "cuti": _cari_kolom(header_row, "Cuti"),
        "off": _cari_kolom(header_row, "Off"),
    }

    hasil = {}
    for row in all_values[idx_header + 1:]:
        nama = _ambil(row, kolom["nama"]).strip()
        if not nama:
            continue
        hasil[_normalisasi_nama(nama)] = {
            "dp": _ambil(row, kolom["dp"]),
            "jabatan": _ambil(row, kolom["jabatan"]),
            "sakit": _ke_angka(_ambil(row, kolom["sakit"])),
            "izin": _ke_angka(_ambil(row, kolom["izin"])),
            "alpha": _ke_angka(_ambil(row, kolom["alpha"])),
            "tidak_finger": _ke_angka(_ambil(row, kolom["tidak_finger"])),
            "alpha_tdk_finger": _ke_angka(_ambil(row, kolom["alpha_tdk_finger"])),
            "cuti": _ke_angka(_ambil(row, kolom["cuti"])),
            "off": _ke_angka(_ambil(row, kolom["off"])),
        }
    return hasil


_TANDA_DIBALIKKAN = {"ya", "yes", "true", "1"}


def ambil_potongan_terlambat_periode(periode_payroll):
    """Tarik sheet 'KeterlambatanLog', jumlahkan Nominal per nama untuk baris yang cocok
    dengan periode berjalan. Dipanggil sekali di awal proses payroll.

    Kolom 'Periode' di sheet berformat 'YYYY-MM' (mis. '2026-09'), bukan nama bulan.
    Kolom 'Dibalikkan' adalah flag teks ('Ya'/kosong) — kalau 'Ya', baris itu dianggap
    batal sepenuhnya (kontribusi 0), bukan pengurangan angka seperti nama kolomnya."""
    spreadsheet = buka_spreadsheet_absensi()
    worksheet = spreadsheet.worksheet(NAMA_SHEET_KETERLAMBATAN)
    baris_list = ambil_semua_baris(worksheet)

    kode_periode = f"{periode_payroll.tahun:04d}-{periode_payroll.bulan:02d}"
    hasil = {}
    for baris in baris_list:
        periode_baris = str(baris.get("Periode", "")).strip()
        if periode_baris != kode_periode:
            continue
        nama = baris.get("Nama")
        if not nama:
            continue

        dibalikkan_raw = str(baris.get("Dibalikkan", "")).strip().lower()
        if dibalikkan_raw in _TANDA_DIBALIKKAN:
            continue  # potongan dibatalkan sepenuhnya, tidak dihitung

        nominal = _ke_angka(baris.get("Nominal"))
        key = _normalisasi_nama(nama)
        hasil[key] = hasil.get(key, 0) + nominal
    return hasil

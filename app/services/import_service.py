import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

import openpyxl

from app.models import Karyawan, JenisReward, ReasonClaim, Jabatan


class BarisImportError(Exception):
    pass


def _baca_baris_xlsx(file_storage):
    workbook = openpyxl.load_workbook(file_storage, read_only=True, data_only=True)
    sheet = workbook.active
    baris_iter = sheet.iter_rows(values_only=True)
    header = [str(h).strip() if h else "" for h in next(baris_iter)]
    for baris in baris_iter:
        if baris is None or all(v is None for v in baris):
            continue
        yield dict(zip(header, baris))


def _baca_baris_csv(file_storage):
    teks = file_storage.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(teks))
    for baris in reader:
        yield baris


def baca_baris_file(file_storage):
    nama_file = (file_storage.filename or "").lower()
    if nama_file.endswith(".csv"):
        return list(_baca_baris_csv(file_storage))
    return list(_baca_baris_xlsx(file_storage))


def _ke_desimal(nilai):
    if nilai in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(nilai).replace(",", "."))
    except InvalidOperation:
        return Decimal("0")


def parse_template_nik_nominal_keterangan(file_storage):
    """Parse template generik: kolom NIK, Nominal, Keterangan (nama kolom fleksibel:
    'NIK'/'NIK Karyawan', 'Nominal'/'Jumlah', 'Keterangan'/'Ket').

    Mengembalikan (baris_valid, nik_tidak_ditemukan) di mana baris_valid adalah
    list of (karyawan, nominal, keterangan).
    """
    baris_list = baca_baris_file(file_storage)

    peta_karyawan = {k.nik_karyawan.strip().lower(): k for k in Karyawan.query.all()}

    baris_valid = []
    nik_tidak_ditemukan = []

    for baris in baris_list:
        nik = str(
            baris.get("NIK") or baris.get("NIK Karyawan") or baris.get("nik") or ""
        ).strip()
        if not nik:
            continue
        nominal = _ke_desimal(baris.get("Nominal") or baris.get("Jumlah") or baris.get("nominal"))
        keterangan = str(
            baris.get("Keterangan") or baris.get("Ket") or baris.get("keterangan") or ""
        ).strip()

        karyawan = peta_karyawan.get(nik.lower())
        if karyawan is None:
            nik_tidak_ditemukan.append(nik)
            continue
        baris_valid.append((karyawan, nominal, keterangan))

    return baris_valid, nik_tidak_ditemukan


def parse_template_reward(file_storage):
    """Parse template reward: kolom NIK, Jenis Reward, Nominal, Keterangan.

    Mengembalikan (baris_valid, masalah) di mana baris_valid adalah
    list of (karyawan, jenis_reward, nominal, keterangan), dan masalah adalah
    list string berisi NIK tidak ditemukan / jenis reward tidak dikenal.
    """
    baris_list = baca_baris_file(file_storage)

    peta_karyawan = {k.nik_karyawan.strip().lower(): k for k in Karyawan.query.all()}
    peta_jenis = {j.nama.strip().lower(): j for j in JenisReward.query.all()}

    baris_valid = []
    masalah = []

    for baris in baris_list:
        nik = str(baris.get("NIK") or baris.get("NIK Karyawan") or "").strip()
        if not nik:
            continue
        nama_jenis = str(baris.get("Jenis Reward") or baris.get("Jenis") or "").strip()
        nominal = _ke_desimal(baris.get("Nominal") or baris.get("Jumlah"))
        keterangan = str(baris.get("Keterangan") or baris.get("Ket") or "").strip()

        karyawan = peta_karyawan.get(nik.lower())
        if karyawan is None:
            masalah.append(f"NIK '{nik}' tidak ditemukan")
            continue

        jenis_reward = peta_jenis.get(nama_jenis.lower())
        if jenis_reward is None:
            masalah.append(f"Jenis reward '{nama_jenis}' (baris NIK {nik}) tidak dikenal, tambahkan dulu di master jenis reward")
            continue

        baris_valid.append((karyawan, jenis_reward, nominal, keterangan))

    return baris_valid, masalah


def _ke_tanggal(nilai):
    if not nilai:
        return None
    if hasattr(nilai, "date"):
        return nilai.date() if hasattr(nilai, "hour") else nilai
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(nilai).strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_template_prediksi_berita_acara(file_storage):
    """Template dari tim: AWB, NIK Karyawan, Nominal, Reason Claim, Tanggal, Keterangan.

    Mengembalikan (baris_valid, masalah). baris_valid = list of dict dengan key
    awb, karyawan, nominal, reason_claim, tanggal, keterangan.
    """
    baris_list = baca_baris_file(file_storage)
    peta_karyawan = {k.nik_karyawan.strip().lower(): k for k in Karyawan.query.all()}
    peta_reason = {r.nama.strip().lower(): r for r in ReasonClaim.query.all()}

    baris_valid = []
    masalah = []

    for baris in baris_list:
        awb = str(baris.get("AWB") or "").strip()
        if not awb:
            continue
        nik = str(baris.get("NIK Karyawan") or baris.get("NIK") or "").strip()
        karyawan = peta_karyawan.get(nik.lower())
        if karyawan is None:
            masalah.append(f"AWB {awb}: NIK '{nik}' tidak ditemukan")
            continue

        nama_reason = str(baris.get("Reason Claim") or "").strip()
        reason = peta_reason.get(nama_reason.lower())
        if reason is None:
            masalah.append(f"AWB {awb}: Reason Claim '{nama_reason}' tidak dikenal, tambahkan dulu di master")
            continue

        baris_valid.append(
            {
                "awb": awb,
                "karyawan": karyawan,
                "nominal": _ke_desimal(baris.get("Nominal")),
                "reason_claim": reason,
                "tanggal": _ke_tanggal(baris.get("Tanggal")),
                "keterangan": str(baris.get("Keterangan") or "").strip(),
            }
        )

    return baris_valid, masalah


def parse_template_pusat_berita_acara(file_storage):
    """Template dari pusat (konfirmasi HQ J&T): Periode, Tahun, Jenis Ecommerce, AWB,
    Lokasi Tertagih, Nilai Claim, Mitra, Region, RM, Status Bayar, Keterangan, Reason Claim.

    Mengembalikan (baris_valid, masalah). baris_valid = list of dict mentah per kolom.
    """
    baris_list = baca_baris_file(file_storage)
    peta_reason = {r.nama.strip().lower(): r for r in ReasonClaim.query.all()}

    baris_valid = []
    masalah = []

    for baris in baris_list:
        awb = str(baris.get("AWB") or "").strip()
        if not awb:
            continue

        nama_reason = str(baris.get("Reason Claim") or "").strip()
        reason = peta_reason.get(nama_reason.lower()) if nama_reason else None
        if nama_reason and reason is None:
            masalah.append(f"AWB {awb}: Reason Claim '{nama_reason}' tidak dikenal (dibiarkan kosong)")

        baris_valid.append(
            {
                "awb": awb,
                "periode_pusat": str(baris.get("Periode") or "").strip(),
                "tahun_pusat": str(baris.get("Tahun") or "").strip(),
                "jenis_ecommerce": str(baris.get("Jenis Ecommerce") or "").strip(),
                "lokasi_tertagih": str(baris.get("Lokasi Tertagih") or "").strip(),
                "nominal_pusat": _ke_desimal(baris.get("Nilai Claim")),
                "mitra": str(baris.get("Mitra") or "").strip(),
                "region": str(baris.get("Region") or "").strip(),
                "rm": str(baris.get("RM") or "").strip(),
                "status_bayar": str(baris.get("Status Bayar") or "").strip(),
                "keterangan_pusat": str(baris.get("Keterangan") or "").strip(),
                "reason_claim": reason,
            }
        )

    return baris_valid, masalah


_TANDA_AKTIF_FALSE = {"tidak", "no", "false", "0", "resign", "non aktif", "nonaktif"}


def _ke_bool_aktif(nilai):
    teks = str(nilai or "").strip().lower()
    if teks in _TANDA_AKTIF_FALSE:
        return False
    return True  # default aktif kalau kosong/tidak dikenali


def parse_template_karyawan(file_storage):
    """Template import Karyawan. Kolom wajib: Kode DP, NIK Karyawan, Nama, Jabatan,
    Tanggal Join. Kolom opsional: NPWP, NIK KTP, Rekening Bank, Alamat NPWP, Status
    Pajak, Jenis Kelamin, Tanggal Resign, Status Aktif, Limit Deposit Individual,
    Potongan BPJS-TK.

    Pencocokan baris: NIK Karyawan sudah ada -> UPDATE data karyawan tsb; NIK baru ->
    INSERT karyawan baru. Jabatan dicocokkan by nama, harus sudah ada di master.

    Mengembalikan (baris_valid, masalah). baris_valid = list of dict siap dipakai
    untuk create/update Karyawan.
    """
    baris_list = baca_baris_file(file_storage)
    peta_jabatan = {j.nama.strip().lower(): j for j in Jabatan.query.all()}

    baris_valid = []
    masalah = []

    for i, baris in enumerate(baris_list, start=2):  # baris 1 = header
        nik = str(baris.get("NIK Karyawan") or baris.get("NIK") or "").strip()
        nama = str(baris.get("Nama") or "").strip()
        if not nik and not nama:
            continue  # baris kosong, lewati diam-diam
        if not nik or not nama:
            masalah.append(f"Baris {i}: NIK Karyawan dan Nama wajib diisi, dilewati.")
            continue

        nama_jabatan = str(baris.get("Jabatan") or "").strip()
        jabatan = peta_jabatan.get(nama_jabatan.lower())
        if jabatan is None:
            masalah.append(f"Baris {i} (NIK {nik}): Jabatan '{nama_jabatan}' tidak ditemukan, dilewati.")
            continue

        tanggal_join = _ke_tanggal(baris.get("Tanggal Join"))
        if tanggal_join is None:
            masalah.append(f"Baris {i} (NIK {nik}): Tanggal Join kosong/format salah, dilewati.")
            continue

        limit_deposit_raw = baris.get("Limit Deposit Individual")
        limit_deposit = _ke_desimal(limit_deposit_raw) if str(limit_deposit_raw or "").strip() else None

        baris_valid.append(
            {
                "nik_karyawan": nik,
                "nama": nama,
                "jabatan_id": jabatan.id,
                "kode_dp": str(baris.get("Kode DP") or "").strip(),
                "npwp": str(baris.get("NPWP") or "").strip(),
                "nik_ktp": str(baris.get("NIK KTP") or "").strip(),
                "rekening_bank": str(baris.get("Rekening Bank") or "").strip(),
                "alamat_npwp": str(baris.get("Alamat NPWP") or "").strip(),
                "status_pajak": str(baris.get("Status Pajak") or "").strip(),
                "jenis_kelamin": (str(baris.get("Jenis Kelamin") or "").strip().upper()[:1] or None),
                "tanggal_join": tanggal_join,
                "tanggal_resign": _ke_tanggal(baris.get("Tanggal Resign")),
                "status_aktif": _ke_bool_aktif(baris.get("Status Aktif")),
                "limit_deposit_individual": limit_deposit,
                "potongan_bpjs_tk": _ke_desimal(baris.get("Potongan BPJS-TK")),
                "tunjangan_masa_kerja": _ke_desimal(baris.get("Tunjangan Masa Kerja")),
            }
        )

    return baris_valid, masalah


def parse_template_absensi_manual(file_storage):
    """Template import Input Absensi Manual. Kolom: NIK, Sakit, Izin, Alpha,
    Tidak Finger, Cuti, Off, Potongan Terlambat. Alpha + Tdk Finger dihitung otomatis
    oleh pemanggil (tidak perlu diisi di template).

    Mengembalikan (baris_valid, masalah). baris_valid = list of (karyawan, data_dict).
    """
    baris_list = baca_baris_file(file_storage)
    peta_karyawan = {k.nik_karyawan.strip().lower(): k for k in Karyawan.query.all()}

    baris_valid = []
    masalah = []

    for i, baris in enumerate(baris_list, start=2):
        nik = str(baris.get("NIK") or baris.get("NIK Karyawan") or "").strip()
        if not nik:
            continue

        karyawan = peta_karyawan.get(nik.lower())
        if karyawan is None:
            masalah.append(f"Baris {i}: NIK '{nik}' tidak ditemukan, dilewati.")
            continue

        baris_valid.append(
            (
                karyawan,
                {
                    "sakit": float(_ke_desimal(baris.get("Sakit"))),
                    "izin": float(_ke_desimal(baris.get("Izin"))),
                    "alpha": float(_ke_desimal(baris.get("Alpha"))),
                    "tidak_finger": float(_ke_desimal(baris.get("Tidak Finger"))),
                    "cuti": float(_ke_desimal(baris.get("Cuti"))),
                    "off": float(_ke_desimal(baris.get("Off"))),
                    "potongan_terlambat": float(_ke_desimal(baris.get("Potongan Terlambat"))),
                },
            )
        )

    return baris_valid, masalah

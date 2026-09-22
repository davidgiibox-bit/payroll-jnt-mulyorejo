from decimal import Decimal

from app.extensions import db
from app.models import TunjanganTransaksi


def catat_perubahan_tunjangan(karyawan, nominal_perubahan, keterangan):
    """Tambah/kurangi Tunjangan Masa Kerja karyawan sebesar nominal_perubahan
    (biasanya kenaikan tahunan, bisa juga negatif untuk koreksi), dicatat sebagai
    TunjanganTransaksi supaya ada riwayat kapan & berapa naiknya."""
    nominal_perubahan = Decimal(nominal_perubahan)
    if nominal_perubahan == 0:
        return None

    karyawan.tunjangan_masa_kerja = Decimal(karyawan.tunjangan_masa_kerja) + nominal_perubahan
    transaksi = TunjanganTransaksi(
        karyawan_id=karyawan.id,
        nominal_perubahan=nominal_perubahan,
        saldo_setelah=karyawan.tunjangan_masa_kerja,
        keterangan=keterangan,
    )
    db.session.add(transaksi)
    return transaksi


def terapkan_kenaikan_massal(perubahan_per_karyawan, keterangan):
    """perubahan_per_karyawan: dict {karyawan: nominal_perubahan}. Baris dengan
    nominal 0 dilewati. Mengembalikan jumlah karyawan yang benar-benar diproses."""
    jumlah = 0
    for karyawan, nominal_perubahan in perubahan_per_karyawan.items():
        if catat_perubahan_tunjangan(karyawan, nominal_perubahan, keterangan) is not None:
            jumlah += 1
    db.session.commit()
    return jumlah

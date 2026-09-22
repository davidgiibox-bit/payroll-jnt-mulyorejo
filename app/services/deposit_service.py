from decimal import Decimal

from app.extensions import db
from app.models import DepositTransaksi
from app.models.deposit import JENIS_PENYESUAIAN


def sesuaikan_saldo_deposit(deposit_saldo, saldo_baru, keterangan, commit=True):
    """Set saldo_terkumpul karyawan langsung ke nilai baru (mis. migrasi saldo dari
    proses manual lama, atau koreksi kesalahan), dicatat sebagai DepositTransaksi
    jenis 'penyesuaian' supaya ada jejak audit — bukan menimpa diam-diam.

    Tidak melakukan apa-apa (return None) kalau saldo_baru sama dengan saldo saat ini."""
    saldo_lama = Decimal(deposit_saldo.saldo_terkumpul)
    saldo_baru = Decimal(saldo_baru)
    delta = saldo_baru - saldo_lama
    if delta == 0:
        return None

    deposit_saldo.saldo_terkumpul = saldo_baru
    db.session.add(
        DepositTransaksi(
            deposit_saldo_id=deposit_saldo.id,
            periode=None,
            jenis=JENIS_PENYESUAIAN,
            nominal=delta,
            saldo_setelah=saldo_baru,
            keterangan=keterangan,
        )
    )
    if commit:
        db.session.commit()
    return delta


def terapkan_sesuaikan_saldo_massal(perubahan_per_deposit_saldo, keterangan):
    """perubahan_per_deposit_saldo: dict {DepositSaldo: saldo_baru}. Baris yang nilainya
    sama dengan saldo saat ini dilewati. Mengembalikan jumlah yang benar-benar diproses."""
    jumlah = 0
    for deposit_saldo, saldo_baru in perubahan_per_deposit_saldo.items():
        if sesuaikan_saldo_deposit(deposit_saldo, saldo_baru, keterangan, commit=False) is not None:
            jumlah += 1
    db.session.commit()
    return jumlah


def hapus_transaksi_deposit(transaksi):
    """Hapus 1 baris riwayat transaksi deposit — HANYA boleh kalau itu transaksi
    TERAKHIR (paling baru) untuk deposit_saldo tsb, supaya saldo_terkumpul tetap
    konsisten dengan sisa riwayat (menghapus baris di tengah akan membuat baris-baris
    sesudahnya jadi tidak match lagi dengan riwayatnya)."""
    deposit_saldo = transaksi.deposit_saldo
    transaksi_terbaru = max(deposit_saldo.transaksi_list, key=lambda t: t.created_at, default=None)
    if transaksi_terbaru is None or transaksi_terbaru.id != transaksi.id:
        raise ValueError("Hanya transaksi TERAKHIR yang boleh dihapus, supaya saldo tetap konsisten.")

    deposit_saldo.saldo_terkumpul = Decimal(deposit_saldo.saldo_terkumpul) - Decimal(transaksi.nominal)
    db.session.delete(transaksi)
    db.session.commit()

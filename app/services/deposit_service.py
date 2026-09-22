from decimal import Decimal

from app.extensions import db
from app.models import DepositTransaksi
from app.models.deposit import JENIS_PENYESUAIAN


def sesuaikan_saldo_deposit(deposit_saldo, saldo_baru, keterangan):
    """Set saldo_terkumpul karyawan langsung ke nilai baru (mis. migrasi saldo dari
    proses manual lama, atau koreksi kesalahan), dicatat sebagai DepositTransaksi
    jenis 'penyesuaian' supaya ada jejak audit — bukan menimpa diam-diam."""
    saldo_lama = Decimal(deposit_saldo.saldo_terkumpul)
    saldo_baru = Decimal(saldo_baru)
    delta = saldo_baru - saldo_lama

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
    db.session.commit()
    return delta

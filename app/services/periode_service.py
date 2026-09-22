from decimal import Decimal

from app.extensions import db
from app.models import (
    KomponenUpload,
    RewardEntry,
    EntertainmentEvent,
    PHLPeriode,
    PHLResiKaryawan,
    PotonganBeritaAcaraPeriode,
    DepositTransaksi,
)
from app.models.periode_payroll import STATUS_FINAL


class PeriodeTidakBisaDihapus(Exception):
    pass


def hapus_periode_payroll(periode):
    """Hapus periode draft beserta SEMUA data turunannya, dan BALIKKAN efek samping
    yang sudah terjadi saat 'Proses' dijalankan sebelumnya:
    - Potongan deposit otomatis periode ini -> saldo_terkumpul karyawan dikembalikan.
    - Potongan Berita Acara/Cicilan periode ini -> saldo_sisa cicilan dikembalikan
      (kasus 'langsung' otomatis bisa diterapkan lagi di periode lain nanti).

    Periode berstatus 'final' TIDAK BOLEH dihapus (data sudah terbit)."""
    if periode.status == STATUS_FINAL:
        raise PeriodeTidakBisaDihapus("Periode yang sudah final tidak bisa dihapus.")

    # 1. Balikkan potongan deposit otomatis periode ini
    kode_periode = f"{periode.tahun:04d}-{periode.bulan:02d}"
    transaksi_deposit = DepositTransaksi.query.filter_by(periode=kode_periode, jenis="otomatis").all()
    for t in transaksi_deposit:
        t.deposit_saldo.saldo_terkumpul = Decimal(t.deposit_saldo.saldo_terkumpul) - Decimal(t.nominal)
        db.session.delete(t)

    # 2. Balikkan potongan Berita Acara/Cicilan periode ini
    potongan_ba_list = PotonganBeritaAcaraPeriode.query.filter_by(periode_payroll_id=periode.id).all()
    for p in potongan_ba_list:
        kasus = p.kasus
        if kasus.cicilan is not None:
            kasus.cicilan.saldo_sisa = Decimal(kasus.cicilan.saldo_sisa) + Decimal(p.nominal)
            if kasus.cicilan.status == "lunas":
                kasus.cicilan.status = "aktif"
        db.session.delete(p)

    # 3. Hapus komponen upload, reward (termasuk peserta entertainment), event entertainment, PHL
    KomponenUpload.query.filter_by(periode_payroll_id=periode.id).delete()
    RewardEntry.query.filter_by(periode_payroll_id=periode.id).delete()
    EntertainmentEvent.query.filter_by(periode_payroll_id=periode.id).delete()

    phl_periode = PHLPeriode.query.filter_by(periode_payroll_id=periode.id).first()
    if phl_periode:
        PHLResiKaryawan.query.filter_by(phl_periode_id=phl_periode.id).delete()
        db.session.delete(phl_periode)

    # 4. Hapus periode itu sendiri (cascade otomatis: slip_gaji_list, absensi_ringkasan_list)
    label = periode.label
    db.session.delete(periode)
    db.session.commit()
    return label

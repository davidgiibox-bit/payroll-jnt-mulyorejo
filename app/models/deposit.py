from datetime import datetime
from app.extensions import db


class PengaturanDeposit(db.Model):
    """Pengaturan global deposit. Didesain single-row (id selalu 1)."""

    __tablename__ = "pengaturan_deposit"

    id = db.Column(db.Integer, primary_key=True)
    default_potongan_bulanan = db.Column(db.Numeric(14, 2), nullable=False, default=200000)
    default_limit_deposit = db.Column(db.Numeric(14, 2), nullable=False, default=4100000)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_current():
        pengaturan = PengaturanDeposit.query.first()
        if pengaturan is None:
            pengaturan = PengaturanDeposit(default_potongan_bulanan=200000, default_limit_deposit=4100000)
            db.session.add(pengaturan)
            db.session.commit()
        return pengaturan


class DepositSaldo(db.Model):
    """Saldo berjalan (running balance) deposit per karyawan."""

    __tablename__ = "deposit_saldo"

    id = db.Column(db.Integer, primary_key=True)
    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False, unique=True)
    karyawan = db.relationship("Karyawan", back_populates="deposit_saldo")

    saldo_terkumpul = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transaksi_list = db.relationship(
        "DepositTransaksi", back_populates="deposit_saldo", cascade="all, delete-orphan"
    )

    def limit_efektif(self):
        """Limit deposit karyawan: pakai override individual kalau ada (termasuk 0,
        yang berarti karyawan itu tidak dipotong sama sekali), kalau tidak pakai
        limit default global (terpisah dari nominal potongan bulanan default)."""
        if self.karyawan.limit_deposit_individual is not None:
            return self.karyawan.limit_deposit_individual
        return PengaturanDeposit.get_current().default_limit_deposit


JENIS_OTOMATIS = "otomatis"
JENIS_PENYESUAIAN = "penyesuaian"


class DepositTransaksi(db.Model):
    """Log perubahan saldo deposit — baik potongan otomatis tiap periode payroll,
    maupun penyesuaian manual (mis. migrasi saldo dari proses lama)."""

    __tablename__ = "deposit_transaksi"

    id = db.Column(db.Integer, primary_key=True)
    deposit_saldo_id = db.Column(db.Integer, db.ForeignKey("deposit_saldo.id"), nullable=False)
    deposit_saldo = db.relationship("DepositSaldo", back_populates="transaksi_list")

    periode = db.Column(db.String(7), nullable=True)  # format "YYYY-MM", kosong utk penyesuaian manual
    jenis = db.Column(db.String(20), nullable=False, default=JENIS_OTOMATIS)
    nominal = db.Column(db.Numeric(14, 2), nullable=False)  # bisa negatif utk penyesuaian turun
    saldo_setelah = db.Column(db.Numeric(14, 2), nullable=False)
    keterangan = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DepositTransaksi {self.jenis} {self.periode}: {self.nominal}>"

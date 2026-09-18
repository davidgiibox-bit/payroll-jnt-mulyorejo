from datetime import datetime
from app.extensions import db


class PHLPeriode(db.Model):
    """Total biaya PHL & total paket yang dihandle pada satu periode — dipakai untuk
    menghitung biaya per paket, lalu dikalikan jumlah resi tiap karyawan."""

    __tablename__ = "phl_periode"
    __table_args__ = (db.UniqueConstraint("periode_payroll_id", name="uq_phl_periode"),)

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    total_biaya = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_paket = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resi_list = db.relationship("PHLResiKaryawan", back_populates="phl_periode", cascade="all, delete-orphan")

    @property
    def biaya_per_paket(self):
        if not self.total_paket:
            return 0
        return self.total_biaya / self.total_paket


class PHLResiKaryawan(db.Model):
    """Jumlah resi yang dipickup tiap karyawan pada periode ybs — angka final dari tim
    (manual), belum terintegrasi otomatis ke sistem pickup resi terpisah."""

    __tablename__ = "phl_resi_karyawan"
    __table_args__ = (db.UniqueConstraint("phl_periode_id", "karyawan_id", name="uq_phl_resi_karyawan"),)

    id = db.Column(db.Integer, primary_key=True)

    phl_periode_id = db.Column(db.Integer, db.ForeignKey("phl_periode.id"), nullable=False)
    phl_periode = db.relationship("PHLPeriode", back_populates="resi_list")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    jumlah_resi = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<PHLResiKaryawan karyawan={self.karyawan_id} resi={self.jumlah_resi}>"

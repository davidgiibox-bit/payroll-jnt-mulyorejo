from datetime import datetime
from app.extensions import db


class JenisTambahan(db.Model):
    """Master data jenis tambahan gaji (di luar Reward, Insentif, THR) -- mis. Tambahan
    Mitra, Lembur, KPI COD, Tambahan Grade, Tambahan Lain -- dikelola admin, bisa
    nambah/hapus jenis kapan saja."""

    __tablename__ = "jenis_tambahan"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<JenisTambahan {self.nama}>"


class TambahanEntry(db.Model):
    """Satu baris tambahan gaji untuk satu karyawan pada satu periode."""

    __tablename__ = "tambahan_entry"

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    jenis_tambahan_id = db.Column(db.Integer, db.ForeignKey("jenis_tambahan.id"), nullable=False)
    jenis_tambahan = db.relationship("JenisTambahan")

    nominal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    keterangan = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TambahanEntry karyawan={self.karyawan_id} nominal={self.nominal}>"

from datetime import datetime
from app.extensions import db


class JenisPotonganLainnya(db.Model):
    """Master data jenis Potongan Lainnya (mis. Denda Administrasi, Pemotongan Insentif
    Admin, Pemotongan Penyesuaian PPPM, dst) -- dikelola admin, bisa nambah/hapus kapan
    saja. TIDAK termasuk Denda Terlambat/Cicilan BA/Potongan PHL/Potongan Entertainment,
    karena masing-masing sudah punya komponen tersendiri di sistem."""

    __tablename__ = "jenis_potongan_lainnya"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<JenisPotonganLainnya {self.nama}>"


class PotonganLainnyaEntry(db.Model):
    """Satu baris Potongan Lainnya untuk satu karyawan pada satu periode."""

    __tablename__ = "potongan_lainnya_entry"

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    jenis_potongan_lainnya_id = db.Column(db.Integer, db.ForeignKey("jenis_potongan_lainnya.id"), nullable=False)
    jenis_potongan_lainnya = db.relationship("JenisPotonganLainnya")

    nominal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    keterangan = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PotonganLainnyaEntry karyawan={self.karyawan_id} nominal={self.nominal}>"

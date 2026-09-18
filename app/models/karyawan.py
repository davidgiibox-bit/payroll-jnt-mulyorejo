from datetime import datetime
from app.extensions import db


class Karyawan(db.Model):
    __tablename__ = "karyawan"

    id = db.Column(db.Integer, primary_key=True)

    kode_dp = db.Column(db.String(20), nullable=False)
    nik_karyawan = db.Column(db.String(30), nullable=False, unique=True)
    nama = db.Column(db.String(150), nullable=False)

    jabatan_id = db.Column(db.Integer, db.ForeignKey("jabatan.id"), nullable=False)
    jabatan = db.relationship("Jabatan", back_populates="karyawan_list")

    npwp = db.Column(db.String(30))
    nik_ktp = db.Column(db.String(30))
    rekening_bank = db.Column(db.String(100))
    alamat_npwp = db.Column(db.Text)

    status_pajak = db.Column(db.String(10))  # TK/0, K/0, K/1, dst — referensi saja
    jenis_kelamin = db.Column(db.String(1))  # L / P

    tanggal_join = db.Column(db.Date)
    tanggal_resign = db.Column(db.Date, nullable=True)
    status_aktif = db.Column(db.Boolean, default=True, nullable=False)

    limit_deposit_individual = db.Column(db.Numeric(14, 2), nullable=True)  # override default global
    potongan_bpjs_tk = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="karyawan", uselist=False)
    deposit_saldo = db.relationship("DepositSaldo", back_populates="karyawan", uselist=False)

    def __repr__(self):
        return f"<Karyawan {self.nik_karyawan} - {self.nama}>"

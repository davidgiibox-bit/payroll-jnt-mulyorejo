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
    tunjangan_masa_kerja = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # nominal manual, di-update tim per tahun

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="karyawan", uselist=False)
    deposit_saldo = db.relationship("DepositSaldo", back_populates="karyawan", uselist=False)

    tunjangan_transaksi_list = db.relationship(
        "TunjanganTransaksi", back_populates="karyawan", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Karyawan {self.nik_karyawan} - {self.nama}>"


class TunjanganTransaksi(db.Model):
    """Riwayat perubahan Tunjangan Masa Kerja karyawan — dicatat tiap kali ada
    kenaikan tahunan (nominalnya beda-beda tiap karyawan & tiap tahun, di-input
    manual oleh tim, bukan formula otomatis)."""

    __tablename__ = "tunjangan_transaksi"

    id = db.Column(db.Integer, primary_key=True)

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan", back_populates="tunjangan_transaksi_list")

    nominal_perubahan = db.Column(db.Numeric(14, 2), nullable=False)  # bisa negatif utk koreksi
    saldo_setelah = db.Column(db.Numeric(14, 2), nullable=False)
    keterangan = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TunjanganTransaksi karyawan={self.karyawan_id} nominal={self.nominal_perubahan}>"

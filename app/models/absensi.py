from datetime import datetime
from app.extensions import db


class AbsensiRingkasanKaryawan(db.Model):
    """Cache ringkasan absensi per karyawan per periode, ditarik dari Google Sheets sekali
    saat payroll diproses (bukan sinkronisasi harian). Sesuai prinsip minim penyimpanan
    data mentah — hanya angka rekap yang disimpan, bukan detail Masuk/Keluar harian."""

    __tablename__ = "absensi_ringkasan_karyawan"
    __table_args__ = (
        db.UniqueConstraint("periode_payroll_id", "karyawan_id", name="uq_absensi_periode_karyawan"),
    )

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll", back_populates="absensi_ringkasan_list")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    sakit = db.Column(db.Numeric(6, 1), nullable=False, default=0)
    izin = db.Column(db.Numeric(6, 1), nullable=False, default=0)
    alpha = db.Column(db.Numeric(6, 1), nullable=False, default=0)
    tidak_finger = db.Column(db.Numeric(6, 1), nullable=False, default=0)
    alpha_tdk_finger = db.Column(db.Numeric(6, 1), nullable=False, default=0)
    cuti = db.Column(db.Numeric(6, 1), nullable=False, default=0)
    off = db.Column(db.Numeric(6, 1), nullable=False, default=0)

    potongan_terlambat = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    ditarik_pada = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AbsensiRingkasan karyawan={self.karyawan_id} periode={self.periode_payroll_id}>"

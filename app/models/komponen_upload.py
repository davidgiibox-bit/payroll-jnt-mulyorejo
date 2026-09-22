from datetime import datetime
from app.extensions import db

JENIS_POTONGAN_LAINNYA = "potongan_lainnya"
JENIS_BBM = "bbm"
JENIS_PPH21 = "pph21"
JENIS_THR = "thr"
JENIS_INSENTIF = "insentif"

SEMUA_JENIS = [
    JENIS_POTONGAN_LAINNYA,
    JENIS_BBM,
    JENIS_PPH21,
    JENIS_THR,
    JENIS_INSENTIF,
]

# Field SlipGaji yang diisi dari total per jenis (setelah dijumlah per karyawan per periode)
TARGET_FIELD_SLIP = {
    JENIS_POTONGAN_LAINNYA: "potongan_lainnya",
    JENIS_BBM: "potongan_bbm",
    JENIS_PPH21: "potongan_pph21",
    JENIS_THR: "thr",
    JENIS_INSENTIF: "insentif",
}

# jenis yang menjumlahkan ke field yang sama (insentif) perlu ditangani gabungan saat recalc
JENIS_PER_FIELD = {}
for _jenis, _field in TARGET_FIELD_SLIP.items():
    JENIS_PER_FIELD.setdefault(_field, []).append(_jenis)


class KomponenUpload(db.Model):
    """Baris hasil upload template generik (NIK + nominal + keterangan) untuk komponen
    potongan lainnya, BBM, PPh21, THR, dan 3 skema insentif. Menu upload terpisah per
    komponen di level UI/hak akses, tapi struktur tabelnya sama sehingga cukup satu model."""

    __tablename__ = "komponen_upload"

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    jenis = db.Column(db.String(30), nullable=False)
    nominal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    keterangan = db.Column(db.String(255))

    diunggah_oleh_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KomponenUpload {self.jenis} karyawan={self.karyawan_id} periode={self.periode_payroll_id}>"

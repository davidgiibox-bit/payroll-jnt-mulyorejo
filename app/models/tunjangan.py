from datetime import datetime
from app.extensions import db


class TunjanganMasaKerjaJenjang(db.Model):
    """Tabel berjenjang tunjangan masa kerja berdasarkan rentang masa kerja (dalam bulan).
    Nominal statis sampai diubah manual oleh tim (bukan formula otomatis)."""

    __tablename__ = "tunjangan_masa_kerja_jenjang"

    id = db.Column(db.Integer, primary_key=True)
    min_bulan = db.Column(db.Integer, nullable=False)
    max_bulan = db.Column(db.Integer, nullable=True)  # null = tanpa batas atas
    nominal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    keterangan = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        batas = self.max_bulan if self.max_bulan is not None else "∞"
        return f"<TunjanganJenjang {self.min_bulan}-{batas} bulan: {self.nominal}>"

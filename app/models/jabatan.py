from datetime import datetime
from app.extensions import db


class Jabatan(db.Model):
    __tablename__ = "jabatan"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False, unique=True)
    gaji_pokok_default = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    kena_phl = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    karyawan_list = db.relationship("Karyawan", back_populates="jabatan")
    hak_akses_list = db.relationship("HakAkses", back_populates="jabatan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Jabatan {self.nama}>"

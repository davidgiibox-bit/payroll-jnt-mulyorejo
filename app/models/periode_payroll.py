from datetime import datetime
from app.extensions import db

STATUS_DRAFT = "draft"
STATUS_FINAL = "final"

NAMA_BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


class PeriodePayroll(db.Model):
    """Satu periode payroll bulanan. Sheet absensi terkait bernama 'Rekap {NamaBulan} {tahun}'."""

    __tablename__ = "periode_payroll"
    __table_args__ = (db.UniqueConstraint("tahun", "bulan", name="uq_periode_tahun_bulan"),)

    id = db.Column(db.Integer, primary_key=True)
    tahun = db.Column(db.Integer, nullable=False)
    bulan = db.Column(db.Integer, nullable=False)  # 1-12

    # Override manual nama sheet Rekap — dipakai kalau pemetaan otomatis (nama bulan
    # periode = nama sheet) tidak sesuai, mis. karena cutoff tanggal absensi tim
    # (21-20) belum konsisten dengan penamaan sheet. Kosongkan untuk pakai default.
    nama_sheet_rekap_override = db.Column(db.String(100), nullable=True)

    # Override manual kode periode dipakai untuk cocokkan kolom "Periode" di sheet
    # KeterlambatanLog (formatnya "YYYY-MM"). Kosongkan untuk pakai default (tahun-bulan
    # periode ini apa adanya).
    kode_periode_terlambat_override = db.Column(db.String(20), nullable=True)

    # True kalau absensi periode ini diisi manual (bukan ditarik dari Google Sheets) —
    # dipakai utk trial data bulan lama yang belum ada di sistem absensi/Sheets.
    absensi_manual = db.Column(db.Boolean, nullable=False, default=False)

    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    difinalisasi_at = db.Column(db.DateTime, nullable=True)

    slip_gaji_list = db.relationship("SlipGaji", back_populates="periode", cascade="all, delete-orphan")
    absensi_ringkasan_list = db.relationship(
        "AbsensiRingkasanKaryawan", back_populates="periode", cascade="all, delete-orphan"
    )

    @property
    def nama_bulan(self):
        return NAMA_BULAN[self.bulan - 1]

    @property
    def label(self):
        return f"{self.nama_bulan} {self.tahun}"

    @property
    def nama_sheet_rekap(self):
        if self.nama_sheet_rekap_override:
            return self.nama_sheet_rekap_override
        return f"Rekap {self.nama_bulan} {self.tahun}"

    @property
    def kode_periode_terlambat(self):
        if self.kode_periode_terlambat_override:
            return self.kode_periode_terlambat_override
        return f"{self.tahun:04d}-{self.bulan:02d}"

    def __repr__(self):
        return f"<PeriodePayroll {self.label} ({self.status})>"

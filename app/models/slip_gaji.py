from datetime import datetime
from app.extensions import db

STATUS_DRAFT = "draft"
STATUS_FINAL = "final"


class SlipGaji(db.Model):
    """Slip gaji per karyawan per periode. Nilai master (gaji pokok, tunjangan, BPJS-TK)
    disimpan sebagai snapshot di sini supaya perubahan master di kemudian hari TIDAK
    mengubah slip yang sudah terbit."""

    __tablename__ = "slip_gaji"
    __table_args__ = (
        db.UniqueConstraint("periode_payroll_id", "karyawan_id", name="uq_slip_periode_karyawan"),
    )

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll", back_populates="slip_gaji_list")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    # --- Snapshot master (poin a, b, n) ---
    gaji_pokok_snapshot = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tunjangan_masa_kerja_snapshot = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    # --- Penambahan (sebelum THP) ---
    insentif = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (g)
    thr = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (o)

    # --- Potongan sebelum THP ---
    potongan_deposit = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (c)
    potongan_kehadiran = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (d)
    potongan_terlambat = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (e)
    potongan_lainnya = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (f)
    potongan_pph21 = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (m)
    potongan_bpjs_tk = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (n)

    # --- Penambahan/potongan sesudah THP ---
    reward = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (h) tambahan
    potongan_reward = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (h) potongan, jika ada
    potongan_berita_acara = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (i)/(l)
    potongan_bbm = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (j)
    potongan_phl = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # (k)

    # --- Hasil akhir (disimpan, bukan dihitung ulang saat tampil) ---
    subtotal_thp = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_akhir = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)
    catatan = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    _FIELD_NUMERIK = [
        "gaji_pokok_snapshot", "tunjangan_masa_kerja_snapshot", "insentif", "thr",
        "potongan_deposit", "potongan_kehadiran", "potongan_terlambat", "potongan_lainnya",
        "potongan_pph21", "potongan_bpjs_tk", "reward", "potongan_reward",
        "potongan_berita_acara", "potongan_bbm", "potongan_phl",
    ]

    def hitung_ulang(self):
        """Hitung subtotal_thp dan total_akhir dari komponen yang sudah diisi.
        Dipanggil tiap kali salah satu komponen berubah, sebelum status final.

        Field yang belum pernah di-set (None, sebelum flush pertama ke DB) diperlakukan
        sebagai 0 supaya slip baru yang belum lengkap komponennya tidak error."""
        for nama_field in self._FIELD_NUMERIK:
            if getattr(self, nama_field) is None:
                setattr(self, nama_field, 0)

        penambahan_sebelum_thp = self.gaji_pokok_snapshot + self.tunjangan_masa_kerja_snapshot + self.insentif + self.thr
        potongan_sebelum_thp = (
            self.potongan_deposit
            + self.potongan_kehadiran
            + self.potongan_terlambat
            + self.potongan_lainnya
            + self.potongan_pph21
            + self.potongan_bpjs_tk
        )
        self.subtotal_thp = penambahan_sebelum_thp - potongan_sebelum_thp

        potongan_sesudah_thp = (
            self.potongan_reward
            + self.potongan_berita_acara
            + self.potongan_bbm
            + self.potongan_phl
        )
        self.total_akhir = self.subtotal_thp + self.reward - potongan_sesudah_thp

    def __repr__(self):
        return f"<SlipGaji karyawan={self.karyawan_id} periode={self.periode_payroll_id} status={self.status}>"

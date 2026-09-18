from datetime import datetime
from app.extensions import db

STATUS_PREDIKSI = "prediksi"
STATUS_MENUNGGU_KONFIRMASI = "menunggu_konfirmasi_pusat"
STATUS_FINAL = "final"

KEPUTUSAN_LANGSUNG = "langsung"
KEPUTUSAN_CICIL = "cicil"


class ReasonClaim(db.Model):
    """Master alasan Berita Acara — dropdown dikelola admin, bukan teks bebas."""

    __tablename__ = "reason_claim"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False, unique=True)

    def __repr__(self):
        return f"<ReasonClaim {self.nama}>"


class KasusBeritaAcara(db.Model):
    """Satu kasus Berita Acara, dikunci oleh AWB. Bisa berasal dari prediksi tim,
    data pusat, atau keduanya (dicocokkan otomatis by AWB)."""

    __tablename__ = "kasus_berita_acara"

    id = db.Column(db.Integer, primary_key=True)
    awb = db.Column(db.String(50), nullable=False, unique=True)

    status = db.Column(db.String(30), nullable=False, default=STATUS_PREDIKSI)

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=True)
    karyawan = db.relationship("Karyawan")

    reason_claim_id = db.Column(db.Integer, db.ForeignKey("reason_claim.id"), nullable=True)
    reason_claim = db.relationship("ReasonClaim")

    # --- Dari template prediksi (tim) ---
    nominal_prediksi = db.Column(db.Numeric(14, 2), nullable=True)
    tanggal_prediksi = db.Column(db.Date, nullable=True)
    keterangan_prediksi = db.Column(db.Text)

    # --- Dari template pusat (konfirmasi HQ J&T) ---
    nominal_pusat = db.Column(db.Numeric(14, 2), nullable=True)
    periode_pusat = db.Column(db.String(30))
    tahun_pusat = db.Column(db.String(10))
    jenis_ecommerce = db.Column(db.String(100))
    lokasi_tertagih = db.Column(db.String(150))
    mitra = db.Column(db.String(150))
    region = db.Column(db.String(100))
    rm = db.Column(db.String(100))
    status_bayar = db.Column(db.String(50))
    keterangan_pusat = db.Column(db.Text)

    # --- Keputusan penanganan potongan (diisi tim di halaman review) ---
    keputusan = db.Column(db.String(20), nullable=True)  # 'langsung' / 'cicil'
    jumlah_bulan_cicilan = db.Column(db.Integer, nullable=True)

    nominal_final = db.Column(db.Numeric(14, 2), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cicilan = db.relationship("CicilanBeritaAcara", back_populates="kasus", uselist=False)
    potongan_list = db.relationship("PotonganBeritaAcaraPeriode", back_populates="kasus")

    @property
    def sudah_diterapkan(self):
        return len(self.potongan_list) > 0 or self.cicilan is not None

    def __repr__(self):
        return f"<KasusBeritaAcara awb={self.awb} status={self.status}>"


class CicilanBeritaAcara(db.Model):
    """Entri cicilan terpisah dengan saldo berjalan sendiri. Kalau karyawan punya
    beberapa cicilan aktif sekaligus, semuanya jalan paralel, tidak digabung."""

    __tablename__ = "cicilan_berita_acara"

    id = db.Column(db.Integer, primary_key=True)

    kasus_id = db.Column(db.Integer, db.ForeignKey("kasus_berita_acara.id"), nullable=False, unique=True)
    kasus = db.relationship("KasusBeritaAcara", back_populates="cicilan")

    jumlah_bulan = db.Column(db.Integer, nullable=False)
    nominal_per_bulan = db.Column(db.Numeric(14, 2), nullable=False)
    saldo_sisa = db.Column(db.Numeric(14, 2), nullable=False)

    status = db.Column(db.String(20), nullable=False, default="aktif")  # aktif / lunas

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CicilanBeritaAcara kasus={self.kasus_id} saldo_sisa={self.saldo_sisa}>"


class PotonganBeritaAcaraPeriode(db.Model):
    """Baris potongan Berita Acara/Cicilan yang benar-benar diterapkan ke satu periode
    payroll — baik dari keputusan potong langsung maupun cicilan aktif bulan berjalan."""

    __tablename__ = "potongan_berita_acara_periode"

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    kasus_id = db.Column(db.Integer, db.ForeignKey("kasus_berita_acara.id"), nullable=False)
    kasus = db.relationship("KasusBeritaAcara", back_populates="potongan_list")

    nominal = db.Column(db.Numeric(14, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PotonganBeritaAcaraPeriode kasus={self.kasus_id} periode={self.periode_payroll_id} nominal={self.nominal}>"

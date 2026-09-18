from datetime import datetime
from app.extensions import db


class JenisReward(db.Model):
    """Master data jenis reward — dikelola admin, bisa nambah/hapus jenis kapan saja."""

    __tablename__ = "jenis_reward"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<JenisReward {self.nama}>"


class EntertainmentEvent(db.Model):
    """Satu event entertainment dengan tim — melibatkan banyak karyawan sekaligus,
    nominal per orang di-input manual (bukan dibagi rata otomatis)."""

    __tablename__ = "entertainment_event"

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    deskripsi = db.Column(db.String(255), nullable=False)
    total_biaya = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    peserta_list = db.relationship(
        "RewardEntry", back_populates="entertainment_event", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<EntertainmentEvent {self.deskripsi}>"


class RewardEntry(db.Model):
    """Satu baris reward untuk satu karyawan pada satu periode. Bisa berasal dari upload
    reward biasa (jenis_reward_id terisi) atau dari entertainment (entertainment_event_id
    terisi, nominal per orang di-input manual)."""

    __tablename__ = "reward_entry"

    id = db.Column(db.Integer, primary_key=True)

    periode_payroll_id = db.Column(db.Integer, db.ForeignKey("periode_payroll.id"), nullable=False)
    periode = db.relationship("PeriodePayroll")

    karyawan_id = db.Column(db.Integer, db.ForeignKey("karyawan.id"), nullable=False)
    karyawan = db.relationship("Karyawan")

    jenis_reward_id = db.Column(db.Integer, db.ForeignKey("jenis_reward.id"), nullable=True)
    jenis_reward = db.relationship("JenisReward")

    entertainment_event_id = db.Column(db.Integer, db.ForeignKey("entertainment_event.id"), nullable=True)
    entertainment_event = db.relationship("EntertainmentEvent", back_populates="peserta_list")

    nominal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    keterangan = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RewardEntry karyawan={self.karyawan_id} nominal={self.nominal}>"

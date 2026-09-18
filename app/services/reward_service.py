from app.extensions import db
from app.models import RewardEntry, SlipGaji


def hitung_ulang_reward_slip(periode):
    """Jumlahkan semua RewardEntry (reward biasa + entertainment) per karyawan
    untuk periode ybs, lalu tulis ke SlipGaji.reward."""
    baris = (
        db.session.query(RewardEntry.karyawan_id, db.func.sum(RewardEntry.nominal))
        .filter(RewardEntry.periode_payroll_id == periode.id)
        .group_by(RewardEntry.karyawan_id)
        .all()
    )
    peta_total = {karyawan_id: total for karyawan_id, total in baris}

    for slip in SlipGaji.query.filter_by(periode_payroll_id=periode.id).all():
        slip.reward = peta_total.get(slip.karyawan_id, 0)
        slip.hitung_ulang()
    db.session.commit()

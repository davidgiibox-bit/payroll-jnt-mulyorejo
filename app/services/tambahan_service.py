from app.extensions import db
from app.models import TambahanEntry, SlipGaji


def hitung_ulang_tambahan_slip(periode):
    """Jumlahkan semua TambahanEntry per karyawan untuk periode ybs, lalu tulis ke
    SlipGaji.tambahan."""
    baris = (
        db.session.query(TambahanEntry.karyawan_id, db.func.sum(TambahanEntry.nominal))
        .filter(TambahanEntry.periode_payroll_id == periode.id)
        .group_by(TambahanEntry.karyawan_id)
        .all()
    )
    peta_total = {karyawan_id: total for karyawan_id, total in baris}

    for slip in SlipGaji.query.filter_by(periode_payroll_id=periode.id).all():
        slip.tambahan = peta_total.get(slip.karyawan_id, 0)
        slip.hitung_ulang()
    db.session.commit()

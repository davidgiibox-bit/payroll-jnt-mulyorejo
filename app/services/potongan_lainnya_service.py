from app.extensions import db
from app.models import PotonganLainnyaEntry, SlipGaji


def hitung_ulang_potongan_lainnya_slip(periode):
    """Jumlahkan semua PotonganLainnyaEntry per karyawan untuk periode ybs, lalu tulis ke
    SlipGaji.potongan_lainnya."""
    baris = (
        db.session.query(PotonganLainnyaEntry.karyawan_id, db.func.sum(PotonganLainnyaEntry.nominal))
        .filter(PotonganLainnyaEntry.periode_payroll_id == periode.id)
        .group_by(PotonganLainnyaEntry.karyawan_id)
        .all()
    )
    peta_total = {karyawan_id: total for karyawan_id, total in baris}

    for slip in SlipGaji.query.filter_by(periode_payroll_id=periode.id).all():
        slip.potongan_lainnya = peta_total.get(slip.karyawan_id, 0)
        slip.hitung_ulang()
    db.session.commit()

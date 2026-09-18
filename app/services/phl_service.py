from decimal import Decimal

from app.extensions import db
from app.models import SlipGaji


def hitung_ulang_phl_slip(phl_periode):
    """Potongan per karyawan = biaya_per_paket x jumlah_resi, hanya untuk karyawan
    yang jabatannya kena_phl (configurable). Menulis ke SlipGaji.potongan_phl."""
    periode = phl_periode.periode
    biaya_per_paket = Decimal(phl_periode.biaya_per_paket)

    peta_resi = {resi.karyawan_id: resi.jumlah_resi for resi in phl_periode.resi_list}

    for slip in SlipGaji.query.filter_by(periode_payroll_id=periode.id).all():
        if not slip.karyawan.jabatan.kena_phl:
            slip.potongan_phl = 0
        else:
            jumlah_resi = peta_resi.get(slip.karyawan_id, 0)
            slip.potongan_phl = biaya_per_paket * Decimal(jumlah_resi)
        slip.hitung_ulang()
    db.session.commit()

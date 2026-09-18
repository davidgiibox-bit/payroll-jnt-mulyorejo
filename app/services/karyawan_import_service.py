from app.extensions import db
from app.models import Karyawan, DepositSaldo
from app.services.import_service import parse_template_karyawan


def impor_karyawan(file_storage):
    """Import bulk data karyawan. NIK sudah ada -> update; NIK baru -> insert (plus
    bikin DepositSaldo awal, sama seperti tambah karyawan manual).

    Mengembalikan dict laporan: {'baru': n, 'update': n, 'masalah': [...]}.
    """
    baris_valid, masalah = parse_template_karyawan(file_storage)

    jumlah_baru = 0
    jumlah_update = 0

    for data in baris_valid:
        karyawan = Karyawan.query.filter_by(nik_karyawan=data["nik_karyawan"]).first()
        is_baru = karyawan is None
        if is_baru:
            karyawan = Karyawan(nik_karyawan=data["nik_karyawan"])
            db.session.add(karyawan)

        for field, value in data.items():
            if field == "nik_karyawan":
                continue
            setattr(karyawan, field, value)

        if is_baru:
            db.session.flush()
            db.session.add(DepositSaldo(karyawan_id=karyawan.id, saldo_terkumpul=0))
            jumlah_baru += 1
        else:
            jumlah_update += 1

    db.session.commit()
    return {"baru": jumlah_baru, "update": jumlah_update, "masalah": masalah}

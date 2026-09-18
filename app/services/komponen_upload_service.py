from app.extensions import db
from app.models import KomponenUpload, SlipGaji
from app.models.komponen_upload import TARGET_FIELD_SLIP, JENIS_PER_FIELD
from app.services.import_service import parse_template_nik_nominal_keterangan


def unggah_komponen(periode, jenis, file_storage, user_id):
    """Parse file upload, GANTI seluruh data jenis ini untuk periode ybs (upload ulang
    dianggap koreksi total, bukan tambahan), lalu hitung ulang field SlipGaji terkait.

    Mengembalikan dict laporan: {'jumlah_baris': n, 'nik_tidak_ditemukan': [...]}.
    """
    baris_valid, nik_tidak_ditemukan = parse_template_nik_nominal_keterangan(file_storage)

    KomponenUpload.query.filter_by(periode_payroll_id=periode.id, jenis=jenis).delete()

    for karyawan, nominal, keterangan in baris_valid:
        db.session.add(
            KomponenUpload(
                periode_payroll_id=periode.id,
                karyawan_id=karyawan.id,
                jenis=jenis,
                nominal=nominal,
                keterangan=keterangan,
                diunggah_oleh_user_id=user_id,
            )
        )

    db.session.flush()
    hitung_ulang_field_dari_komponen(periode, TARGET_FIELD_SLIP[jenis])
    db.session.commit()

    return {"jumlah_baris": len(baris_valid), "nik_tidak_ditemukan": nik_tidak_ditemukan}


def hitung_ulang_field_dari_komponen(periode, field_slip):
    """Jumlahkan KomponenUpload per karyawan untuk semua jenis yang bermuara ke field_slip
    yang sama (mis. 3 skema insentif -> field 'insentif'), lalu tulis ke SlipGaji."""
    jenis_list = JENIS_PER_FIELD[field_slip]

    baris = (
        db.session.query(KomponenUpload.karyawan_id, db.func.sum(KomponenUpload.nominal))
        .filter(
            KomponenUpload.periode_payroll_id == periode.id,
            KomponenUpload.jenis.in_(jenis_list),
        )
        .group_by(KomponenUpload.karyawan_id)
        .all()
    )
    peta_total = {karyawan_id: total for karyawan_id, total in baris}

    for slip in SlipGaji.query.filter_by(periode_payroll_id=periode.id).all():
        setattr(slip, field_slip, peta_total.get(slip.karyawan_id, 0))
        slip.hitung_ulang()

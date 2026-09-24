from decimal import Decimal

from app.extensions import db
from app.models import KasusBeritaAcara, CicilanBeritaAcara, PotonganBeritaAcaraPeriode, SlipGaji, PeriodePayroll
from app.models.berita_acara import (
    STATUS_PREDIKSI,
    STATUS_MENUNGGU_KONFIRMASI,
    STATUS_FINAL,
    KEPUTUSAN_LANGSUNG,
)
from app.services.import_service import parse_template_prediksi_berita_acara, parse_template_pusat_berita_acara


def impor_prediksi(file_storage):
    """Import template prediksi dari tim. AWB baru -> kasus baru (status prediksi,
    langsung ter-assign ke karyawan, keputusan default 'langsung'). AWB yang sudah
    ada -> perbarui data prediksinya (asumsi tim mengoreksi input sebelumnya)."""
    baris_valid, masalah = parse_template_prediksi_berita_acara(file_storage)

    jumlah_baru = 0
    jumlah_update = 0

    for baris in baris_valid:
        kasus = KasusBeritaAcara.query.filter_by(awb=baris["awb"]).first()
        if kasus is None:
            kasus = KasusBeritaAcara(awb=baris["awb"], status=STATUS_PREDIKSI, keputusan=KEPUTUSAN_LANGSUNG)
            db.session.add(kasus)
            jumlah_baru += 1
        else:
            jumlah_update += 1

        kasus.karyawan_id = baris["karyawan"].id
        kasus.nominal_prediksi = baris["nominal"]
        kasus.reason_claim_id = baris["reason_claim"].id
        kasus.tanggal_prediksi = baris["tanggal"]
        kasus.keterangan_prediksi = baris["keterangan"]
        if kasus.status == STATUS_PREDIKSI:
            kasus.nominal_final = baris["nominal"]

    db.session.commit()
    return {"baru": jumlah_baru, "update": jumlah_update, "masalah": masalah}


def impor_pusat(file_storage):
    """Import template konfirmasi dari pusat, dicocokkan otomatis by AWB.

    - AWB sudah ada kasus (dari prediksi): update data pusat. Kalau nominal pusat
      beda dari prediksi -> status 'menunggu_konfirmasi_pusat' (perlu keputusan tim
      soal penyesuaian). Kalau sama/tidak ada prediksi sebelumnya -> langsung 'final'.
    - AWB belum pernah ada -> kasus baru, status 'menunggu_konfirmasi_pusat',
      BELUM ter-assign karyawan (perlu assignment manual oleh tim).
    """
    baris_valid, masalah = parse_template_pusat_berita_acara(file_storage)

    jumlah_baru = 0
    jumlah_cocok = 0
    jumlah_selisih = 0

    for baris in baris_valid:
        kasus = KasusBeritaAcara.query.filter_by(awb=baris["awb"]).first()
        field_pusat = {k: v for k, v in baris.items() if k not in ("awb", "reason_claim")}

        if kasus is None:
            kasus = KasusBeritaAcara(awb=baris["awb"], status=STATUS_MENUNGGU_KONFIRMASI)
            db.session.add(kasus)
            for k, v in field_pusat.items():
                setattr(kasus, k, v)
            if baris["reason_claim"]:
                kasus.reason_claim_id = baris["reason_claim"].id
            kasus.nominal_final = baris["nominal_pusat"]
            jumlah_baru += 1
            continue

        for k, v in field_pusat.items():
            setattr(kasus, k, v)
        if baris["reason_claim"] and kasus.reason_claim_id is None:
            kasus.reason_claim_id = baris["reason_claim"].id

        if kasus.nominal_prediksi is not None and kasus.nominal_prediksi != baris["nominal_pusat"]:
            kasus.status = STATUS_MENUNGGU_KONFIRMASI
            jumlah_selisih += 1
        else:
            kasus.status = STATUS_FINAL
            kasus.nominal_final = baris["nominal_pusat"]
            jumlah_cocok += 1

    db.session.commit()
    return {
        "baru": jumlah_baru,
        "cocok": jumlah_cocok,
        "selisih": jumlah_selisih,
        "masalah": masalah,
    }


def ubah_keputusan_massal(daftar_kasus, keputusan, jumlah_bulan=None):
    """Terapkan keputusan yang sama (cicil N bulan / potong langsung) ke banyak kasus
    sekaligus. Kasus yang sudah pernah dipotong atau belum ter-assign karyawan dilewati.
    Semua perubahan dicommit sekali di akhir. Mengembalikan (jumlah_berhasil, jumlah_dilewati)."""
    berhasil = 0
    dilewati = 0
    for kasus in daftar_kasus:
        if kasus.sudah_diterapkan or kasus.karyawan_id is None:
            dilewati += 1
            continue
        if keputusan == "cicil":
            buat_cicilan(kasus, jumlah_bulan, commit=False)
        else:
            if kasus.cicilan:
                db.session.delete(kasus.cicilan)
                db.session.flush()
            kasus.keputusan = KEPUTUSAN_LANGSUNG
            kasus.jumlah_bulan_cicilan = None
        berhasil += 1
    db.session.commit()
    return berhasil, dilewati


def buat_cicilan(kasus, jumlah_bulan, commit=True):
    """Ubah keputusan kasus jadi cicil, buat entri CicilanBeritaAcara dengan saldo
    berjalan sendiri. Kalau sebelumnya sudah ada cicilan, hapus & buat ulang
    (hanya boleh dipanggil sebelum ada potongan yang sudah diterapkan ke periode)."""
    if kasus.sudah_diterapkan:
        raise ValueError("Kasus ini sudah pernah diterapkan ke suatu periode, tidak bisa diubah lagi.")

    nominal_total = Decimal(kasus.nominal_final or 0)
    nominal_per_bulan = (nominal_total / jumlah_bulan).quantize(Decimal("1"))

    if kasus.cicilan:
        db.session.delete(kasus.cicilan)
        db.session.flush()

    cicilan = CicilanBeritaAcara(
        kasus_id=kasus.id,
        jumlah_bulan=jumlah_bulan,
        nominal_per_bulan=nominal_per_bulan,
        saldo_sisa=nominal_total,
        status="aktif",
    )
    db.session.add(cicilan)
    kasus.keputusan = "cicil"
    kasus.jumlah_bulan_cicilan = jumlah_bulan
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return cicilan


def dampak_periode_berjalan(kasus):
    """Nominal yang BENAR-BENAR akan kepotong kalau 'Terapkan ke Periode Ini' dijalankan
    sekarang. Dipakai halaman Review supaya total per karyawan tidak menampilkan nilai
    klaim PENUH (nominal_final) untuk kasus yang sedang dicicil -- yang sungguhan
    dipotong per periode cuma nominal_per_bulan (atau sisa saldo penuh kalau karyawan
    resign), sama seperti logika di terapkan_potongan_periode() di bawah."""
    if kasus.cicilan and kasus.cicilan.status == "aktif":
        karyawan = kasus.karyawan
        if karyawan is not None and karyawan.status_aktif is False:
            return Decimal(kasus.cicilan.saldo_sisa)
        return min(Decimal(kasus.cicilan.nominal_per_bulan), Decimal(kasus.cicilan.saldo_sisa))
    return Decimal(kasus.nominal_final or 0)


def _cutoff_kasus_backfill(periode):
    """Kalau periode ini sedang diproses ULANG (backfill) setelah periode yang lebih
    baru SUDAH LEBIH DULU menerapkan potongan Berita Acara, kembalikan waktu paling
    awal potongan diterapkan ke periode yang lebih baru itu. Dipakai untuk membatasi
    kasus_langsung/cicilan yang diambil supaya kasus BARU yang dibuat setelah periode
    lebih baru itu diproses tidak ikut "nyasar" ke periode lama ini.

    Mengembalikan None kalau belum ada periode lebih baru yang diproses (alur normal,
    proses berurutan maju) -- di situ tidak ada pembatasan tambahan."""
    return (
        db.session.query(db.func.min(PotonganBeritaAcaraPeriode.created_at))
        .join(PeriodePayroll, PotonganBeritaAcaraPeriode.periode_payroll_id == PeriodePayroll.id)
        .filter(
            db.or_(
                PeriodePayroll.tahun > periode.tahun,
                db.and_(PeriodePayroll.tahun == periode.tahun, PeriodePayroll.bulan > periode.bulan),
            )
        )
        .scalar()
    )


def terapkan_potongan_periode(periode):
    """Terapkan potongan Berita Acara/Cicilan ke periode ybs:
    - Kasus keputusan='langsung' yang belum pernah diterapkan -> potong penuh sekali.
    - Cicilan aktif -> potong nominal_per_bulan (atau sisa saldo kalau lebih kecil),
      SEKALI per periode (idempotent).
    Karyawan resign dengan cicilan belum lunas: sisa cicilan langsung dipotong penuh
    dari periode ini (gaji terakhir); kalau nominalnya melebihi slip, sistem tetap
    mencatat potongan penuh dan memberi peringatan supaya tim cek saldo deposit
    karyawan tsb secara manual.
    """
    peringatan = []
    cutoff_backfill = _cutoff_kasus_backfill(periode)

    kasus_langsung = KasusBeritaAcara.query.filter_by(keputusan=KEPUTUSAN_LANGSUNG).all()
    for kasus in kasus_langsung:
        if kasus.sudah_diterapkan or kasus.karyawan_id is None:
            continue
        if cutoff_backfill is not None and kasus.created_at >= cutoff_backfill:
            # Periode ini sedang di-backfill (ada periode lebih baru yang sudah lebih
            # dulu diproses) -- kasus yang dibuat SETELAH periode lebih baru itu
            # diproses bukan bagian dari periode lama ini, biarkan menunggu periode
            # berjalan yang sebenarnya.
            continue
        nominal = Decimal(kasus.nominal_final or 0)
        db.session.add(
            PotonganBeritaAcaraPeriode(
                periode_payroll_id=periode.id,
                karyawan_id=kasus.karyawan_id,
                kasus_id=kasus.id,
                nominal=nominal,
            )
        )

    cicilan_aktif = CicilanBeritaAcara.query.filter_by(status="aktif").all()
    for cicilan in cicilan_aktif:
        sudah_ada = PotonganBeritaAcaraPeriode.query.filter_by(
            periode_payroll_id=periode.id, kasus_id=cicilan.kasus_id
        ).first()
        if sudah_ada:
            continue
        if cutoff_backfill is not None and cicilan.created_at >= cutoff_backfill:
            continue

        karyawan = cicilan.kasus.karyawan
        resign = karyawan.status_aktif is False

        potongan = Decimal(cicilan.saldo_sisa) if resign else min(
            Decimal(cicilan.nominal_per_bulan), Decimal(cicilan.saldo_sisa)
        )
        if resign and potongan > 0:
            peringatan.append(
                f"{karyawan.nama}: karyawan resign dengan sisa cicilan Rp{potongan:,.0f}, "
                f"dipotong penuh periode ini — cek juga saldo deposit kalau slip tidak cukup."
            )

        if potongan <= 0:
            continue

        db.session.add(
            PotonganBeritaAcaraPeriode(
                periode_payroll_id=periode.id,
                karyawan_id=cicilan.kasus.karyawan_id,
                kasus_id=cicilan.kasus_id,
                nominal=potongan,
            )
        )
        cicilan.saldo_sisa = Decimal(cicilan.saldo_sisa) - potongan
        if cicilan.saldo_sisa <= 0:
            cicilan.status = "lunas"

    db.session.flush()
    _hitung_ulang_slip(periode)
    db.session.commit()
    return {"peringatan": peringatan}


def _hitung_ulang_slip(periode):
    baris = (
        db.session.query(PotonganBeritaAcaraPeriode.karyawan_id, db.func.sum(PotonganBeritaAcaraPeriode.nominal))
        .filter(PotonganBeritaAcaraPeriode.periode_payroll_id == periode.id)
        .group_by(PotonganBeritaAcaraPeriode.karyawan_id)
        .all()
    )
    peta_total = {karyawan_id: total for karyawan_id, total in baris}
    for slip in SlipGaji.query.filter_by(periode_payroll_id=periode.id).all():
        slip.potongan_berita_acara = peta_total.get(slip.karyawan_id, 0)
        slip.hitung_ulang()

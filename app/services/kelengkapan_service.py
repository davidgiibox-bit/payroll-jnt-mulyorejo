from app.models import (
    AbsensiRingkasanKaryawan,
    KomponenUpload,
    RewardEntry,
    EntertainmentEvent,
    PHLPeriode,
    PotonganBeritaAcaraPeriode,
)
from app.models.komponen_upload import (
    JENIS_POTONGAN_LAINNYA,
    JENIS_BBM,
    JENIS_PPH21,
    JENIS_THR,
    JENIS_INSENTIF_BO_DP,
    JENIS_INSENTIF_SPRINTER,
    JENIS_INSENTIF_KURIR,
)


def ambil_status_kelengkapan(periode):
    """Ringkasan status kelengkapan tiap komponen untuk satu periode payroll,
    dipakai di dashboard supaya tim gampang lihat apa yang masih kurang."""

    def jumlah_upload(jenis):
        return KomponenUpload.query.filter_by(periode_payroll_id=periode.id, jenis=jenis).count()

    return [
        {
            "label": "Absensi (dari Google Sheets)",
            "jumlah": AbsensiRingkasanKaryawan.query.filter_by(periode_payroll_id=periode.id).count(),
        },
        {"label": "Potongan Lainnya", "jumlah": jumlah_upload(JENIS_POTONGAN_LAINNYA)},
        {"label": "BBM", "jumlah": jumlah_upload(JENIS_BBM)},
        {"label": "PPh21", "jumlah": jumlah_upload(JENIS_PPH21)},
        {"label": "THR", "jumlah": jumlah_upload(JENIS_THR)},
        {"label": "Insentif BO DP", "jumlah": jumlah_upload(JENIS_INSENTIF_BO_DP)},
        {"label": "Insentif Sprinter", "jumlah": jumlah_upload(JENIS_INSENTIF_SPRINTER)},
        {"label": "Insentif Kurir", "jumlah": jumlah_upload(JENIS_INSENTIF_KURIR)},
        {
            "label": "Reward",
            "jumlah": RewardEntry.query.filter_by(
                periode_payroll_id=periode.id, entertainment_event_id=None
            ).count(),
        },
        {
            "label": "Entertainment (event)",
            "jumlah": EntertainmentEvent.query.filter_by(periode_payroll_id=periode.id).count(),
        },
        {
            "label": "PHL",
            "jumlah": 1 if PHLPeriode.query.filter_by(periode_payroll_id=periode.id).first() else 0,
        },
        {
            "label": "Berita Acara / Cicilan",
            "jumlah": PotonganBeritaAcaraPeriode.query.filter_by(periode_payroll_id=periode.id).count(),
        },
    ]

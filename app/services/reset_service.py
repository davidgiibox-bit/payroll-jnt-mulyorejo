from app.extensions import db
from app.cli import DAFTAR_MENU_AWAL, _buat_superadmin
from app.models import Menu
import os


def reset_total_database():
    """BAHAYA: hapus SEMUA data di SEMUA tabel, lalu seed ulang menu awal & superadmin
    dari env var SUPERADMIN_USERNAME/PASSWORD/NAMA (kalau diisi). Dipakai HANYA untuk
    uji coba ulang dari nol sebelum go-live sungguhan — bukan operasi rutin.

    Tidak bisa dibatalkan. Pemanggil (route) wajib sudah minta konfirmasi eksplisit
    sebelum memanggil fungsi ini."""
    # Hapus semua baris di semua tabel, urutan dibalik dari urutan dependency FK
    # supaya tidak kena constraint error.
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

    # Seed ulang menu awal
    for kode, nama, urutan in DAFTAR_MENU_AWAL:
        db.session.add(Menu(kode_menu=kode, nama_menu=nama, urutan=urutan))
    db.session.commit()

    # Buat ulang superadmin dari env var, kalau diisi
    username = os.environ.get("SUPERADMIN_USERNAME")
    password = os.environ.get("SUPERADMIN_PASSWORD")
    nama = os.environ.get("SUPERADMIN_NAMA", "Admin")
    pesan_superadmin = "SUPERADMIN_USERNAME/PASSWORD tidak diisi, superadmin belum dibuat ulang."
    if username and password:
        pesan_superadmin = _buat_superadmin(username, password, nama)

    return pesan_superadmin

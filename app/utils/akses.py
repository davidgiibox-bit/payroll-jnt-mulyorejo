from functools import wraps
from flask import abort
from flask_login import current_user
from app.models.akses import HakAkses, LEVEL_TIDAK_ADA, LEVEL_LIHAT, LEVEL_EDIT, LEVEL_APPROVE

_URUTAN_LEVEL = {
    LEVEL_TIDAK_ADA: 0,
    LEVEL_LIHAT: 1,
    LEVEL_EDIT: 2,
    LEVEL_APPROVE: 3,
}


def level_akses_user(kode_menu):
    """Ambil level akses user saat ini untuk suatu menu, berdasarkan jabatan karyawan yang login."""
    if not current_user.is_authenticated:
        return LEVEL_TIDAK_ADA
    if current_user.is_superadmin:
        return LEVEL_APPROVE

    jabatan_id = current_user.karyawan.jabatan_id
    hak = HakAkses.query.filter_by(jabatan_id=jabatan_id).join(HakAkses.menu).filter_by(
        kode_menu=kode_menu
    ).first()
    return hak.level_akses if hak else LEVEL_TIDAK_ADA


def punya_akses_minimal(kode_menu, level_minimal):
    level_user = level_akses_user(kode_menu)
    return _URUTAN_LEVEL.get(level_user, 0) >= _URUTAN_LEVEL.get(level_minimal, 0)


def butuh_akses(kode_menu, level_minimal=LEVEL_LIHAT):
    """Decorator untuk route: cek user login punya level akses minimal pada menu tertentu."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not punya_akses_minimal(kode_menu, level_minimal):
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator

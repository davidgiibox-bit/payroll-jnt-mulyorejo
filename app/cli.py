import os
import click
from datetime import date

from app.extensions import db
from app.models import Jabatan, Karyawan, User, Menu, DepositSaldo

DAFTAR_MENU_AWAL = [
    ("master_jabatan", "Data Jabatan", 1),
    ("master_karyawan", "Data Karyawan", 2),
    ("master_deposit", "Deposit", 4),
    ("payroll", "Payroll", 5),
    ("upload_potongan_lainnya", "Upload Potongan Lainnya", 6),
    ("upload_bbm", "Upload BBM", 7),
    ("upload_pph21", "Upload PPh21", 8),
    ("upload_thr", "Upload THR", 9),
    ("upload_insentif_bo_dp", "Upload Insentif BO DP", 10),
    ("upload_insentif_sprinter", "Upload Insentif Sprinter", 11),
    ("upload_insentif_kurir", "Upload Insentif Kurir", 12),
    ("reward", "Reward & Entertainment", 13),
    ("phl", "PHL", 14),
    ("berita_acara", "Berita Acara & Cicilan", 15),
    ("admin_akses", "Hak Akses", 16),
]


def register_cli(app):
    @app.cli.command("seed-menu")
    def seed_menu():
        """Isi tabel menu dengan daftar menu awal sistem (aman dijalankan berulang)."""
        for kode, nama, urutan in DAFTAR_MENU_AWAL:
            if not Menu.query.filter_by(kode_menu=kode).first():
                db.session.add(Menu(kode_menu=kode, nama_menu=nama, urutan=urutan))
        db.session.commit()
        click.echo("Menu awal berhasil di-seed.")

    @app.cli.command("buat-superadmin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--nama", prompt="Nama Lengkap")
    def buat_superadmin(username, password, nama):
        """Buat akun superadmin pertama (PIC), lengkap dengan jabatan & karyawan placeholder."""
        pesan = _buat_superadmin(username, password, nama)
        click.echo(pesan)

    @app.cli.command("seed-superadmin-dari-env")
    def seed_superadmin_dari_env():
        """Buat superadmin dari env var SUPERADMIN_USERNAME/PASSWORD/NAMA kalau belum ada
        user sama sekali. Aman dijalankan berulang (no-op kalau sudah ada user, atau kalau
        env var belum diisi) — dipakai di buildCommand Render supaya tidak perlu Shell
        (Shell tidak tersedia di paket gratis)."""
        if User.query.first() is not None:
            click.echo("Sudah ada user di database, dilewati.")
            return

        username = os.environ.get("SUPERADMIN_USERNAME")
        password = os.environ.get("SUPERADMIN_PASSWORD")
        nama = os.environ.get("SUPERADMIN_NAMA", "Admin")
        if not username or not password:
            click.echo("SUPERADMIN_USERNAME/SUPERADMIN_PASSWORD belum diatur, dilewati.")
            return

        pesan = _buat_superadmin(username, password, nama)
        click.echo(pesan)


def _buat_superadmin(username, password, nama):
    if User.query.filter_by(username=username).first():
        return f"Username '{username}' sudah dipakai."

    jabatan_pic = Jabatan.query.filter_by(nama="PIC").first()
    if jabatan_pic is None:
        jabatan_pic = Jabatan(nama="PIC", gaji_pokok_default=0)
        db.session.add(jabatan_pic)
        db.session.flush()

    karyawan = Karyawan(
        kode_dp="MULYOREJO173",
        nik_karyawan=f"ADMIN-{username}",
        nama=nama,
        jabatan_id=jabatan_pic.id,
        tanggal_join=date.today(),
        status_aktif=True,
        potongan_bpjs_tk=0,
    )
    db.session.add(karyawan)
    db.session.flush()

    db.session.add(DepositSaldo(karyawan_id=karyawan.id, saldo_terkumpul=0))

    user = User(karyawan_id=karyawan.id, username=username, is_superadmin=True)
    user.set_password(password)
    db.session.add(user)

    db.session.commit()
    return f"Superadmin '{username}' berhasil dibuat."

from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.master_jabatan import master_jabatan_bp
    from app.blueprints.master_karyawan import master_karyawan_bp
    from app.blueprints.master_deposit import master_deposit_bp
    from app.blueprints.admin_akses import admin_akses_bp
    from app.blueprints.payroll import payroll_bp
    from app.blueprints.reward import reward_bp
    from app.blueprints.tambahan import tambahan_bp
    from app.blueprints.potongan_lainnya import potongan_lainnya_bp
    from app.blueprints.phl import phl_bp
    from app.blueprints.berita_acara import berita_acara_bp
    from app.blueprints.reset_total import reset_total_bp
    from app.blueprints.upload_generik.factory import buat_blueprint_upload
    from app.models.komponen_upload import (
        JENIS_BBM,
        JENIS_PPH21,
        JENIS_THR,
        JENIS_INSENTIF,
    )

    daftar_blueprint_upload = [
        buat_blueprint_upload("bbm", "upload_bbm", "Potongan BBM", JENIS_BBM, "potongan"),
        buat_blueprint_upload("pph21", "upload_pph21", "Potongan PPh21", JENIS_PPH21, "potongan"),
        buat_blueprint_upload("thr", "upload_thr", "THR", JENIS_THR, "tambah"),
        buat_blueprint_upload("insentif", "upload_insentif", "Insentif", JENIS_INSENTIF, "tambah"),
    ]

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(master_jabatan_bp)
    app.register_blueprint(master_karyawan_bp)
    app.register_blueprint(master_deposit_bp)
    app.register_blueprint(admin_akses_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(reward_bp)
    app.register_blueprint(tambahan_bp)
    app.register_blueprint(potongan_lainnya_bp)
    app.register_blueprint(phl_bp)
    app.register_blueprint(berita_acara_bp)
    app.register_blueprint(reset_total_bp)
    for bp in daftar_blueprint_upload:
        app.register_blueprint(bp)

    from app.utils.akses import level_akses_user

    import os

    def url_statis(filename):
        """URL file statis + ?v=<waktu ubah file>, supaya browser memuat ulang JS/CSS
        yang berubah setelah deploy (bukan memakai versi lama dari cache)."""
        from flask import url_for

        try:
            versi = int(os.path.getmtime(os.path.join(app.static_folder, filename)))
        except OSError:
            versi = 0
        return url_for("static", filename=filename, v=versi)

    @app.context_processor
    def inject_helpers():
        return dict(level_akses_user=level_akses_user, url_statis=url_statis)

    from app.cli import register_cli

    register_cli(app)

    return app

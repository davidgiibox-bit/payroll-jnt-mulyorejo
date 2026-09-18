from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import Jabatan, Menu, HakAkses
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_APPROVE, LEVEL_CHOICES
from app.blueprints.admin_akses import admin_akses_bp

KODE_MENU = "admin_akses"


@admin_akses_bp.route("/", methods=["GET"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_jabatan = Jabatan.query.order_by(Jabatan.nama).all()
    daftar_menu = Menu.query.order_by(Menu.urutan, Menu.nama_menu).all()

    peta_akses = {(h.jabatan_id, h.menu_id): h.level_akses for h in HakAkses.query.all()}

    return render_template(
        "admin_akses/index.html",
        daftar_jabatan=daftar_jabatan,
        daftar_menu=daftar_menu,
        peta_akses=peta_akses,
        level_choices=LEVEL_CHOICES,
    )


@admin_akses_bp.route("/simpan", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_APPROVE)
def simpan():
    daftar_jabatan = Jabatan.query.all()
    daftar_menu = Menu.query.all()
    peta_akses = {(h.jabatan_id, h.menu_id): h for h in HakAkses.query.all()}

    for jabatan in daftar_jabatan:
        for menu in daftar_menu:
            field_name = f"akses_{jabatan.id}_{menu.id}"
            level_dipilih = request.form.get(field_name)
            if level_dipilih not in LEVEL_CHOICES:
                continue
            hak = peta_akses.get((jabatan.id, menu.id))
            if hak is None:
                hak = HakAkses(jabatan_id=jabatan.id, menu_id=menu.id)
                db.session.add(hak)
            hak.level_akses = level_dipilih

    db.session.commit()
    flash("Matriks hak akses berhasil disimpan.", "success")
    return redirect(url_for("admin_akses.index"))

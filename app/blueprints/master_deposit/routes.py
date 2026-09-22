from flask import render_template, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models import PengaturanDeposit, DepositSaldo, Karyawan
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.master_deposit import master_deposit_bp
from app.blueprints.master_deposit.forms import PengaturanDepositForm

KODE_MENU = "master_deposit"


@master_deposit_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    pengaturan = PengaturanDeposit.get_current()
    daftar_saldo = DepositSaldo.query.join(Karyawan).order_by(Karyawan.nama).all()
    return render_template("master_deposit/index.html", pengaturan=pengaturan, daftar_saldo=daftar_saldo)


@master_deposit_bp.route("/pengaturan", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def pengaturan():
    pengaturan_obj = PengaturanDeposit.get_current()
    form = PengaturanDepositForm(obj=pengaturan_obj)
    if form.validate_on_submit():
        pengaturan_obj.default_potongan_bulanan = form.default_potongan_bulanan.data
        pengaturan_obj.default_limit_deposit = form.default_limit_deposit.data
        db.session.commit()
        flash("Pengaturan default deposit berhasil diperbarui.", "success")
        return redirect(url_for("master_deposit.index"))
    return render_template("master_deposit/pengaturan.html", form=form)

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import PengaturanDeposit, DepositSaldo, Karyawan, DepositTransaksi
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT, LEVEL_APPROVE
from app.blueprints.master_deposit import master_deposit_bp
from app.blueprints.master_deposit.forms import PengaturanDepositForm, SesuaikanSaldoForm, SesuaikanSaldoMassalForm
from app.services.deposit_service import (
    sesuaikan_saldo_deposit,
    terapkan_sesuaikan_saldo_massal,
    hapus_transaksi_deposit,
)

KODE_MENU = "master_deposit"


@master_deposit_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    pengaturan = PengaturanDeposit.get_current()
    daftar_saldo = DepositSaldo.query.join(Karyawan).order_by(Karyawan.nama).all()
    return render_template("master_deposit/index.html", pengaturan=pengaturan, daftar_saldo=daftar_saldo)


@master_deposit_bp.route("/<int:karyawan_id>")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def detail(karyawan_id):
    karyawan = Karyawan.query.get_or_404(karyawan_id)
    deposit_saldo = DepositSaldo.query.filter_by(karyawan_id=karyawan.id).first_or_404()
    riwayat = sorted(deposit_saldo.transaksi_list, key=lambda t: t.created_at, reverse=True)
    form = SesuaikanSaldoForm(saldo_baru=deposit_saldo.saldo_terkumpul)
    return render_template(
        "master_deposit/detail.html", karyawan=karyawan, deposit_saldo=deposit_saldo, riwayat=riwayat, form=form
    )


@master_deposit_bp.route("/<int:karyawan_id>/sesuaikan", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def sesuaikan(karyawan_id):
    karyawan = Karyawan.query.get_or_404(karyawan_id)
    deposit_saldo = DepositSaldo.query.filter_by(karyawan_id=karyawan.id).first_or_404()
    form = SesuaikanSaldoForm()
    if form.validate_on_submit():
        sesuaikan_saldo_deposit(deposit_saldo, form.saldo_baru.data, form.keterangan.data.strip())
        flash(f"Saldo deposit '{karyawan.nama}' berhasil disesuaikan menjadi Rp{form.saldo_baru.data:,.0f}.".replace(",", "."), "success")
    else:
        for field_name, error_list in form.errors.items():
            for error in error_list:
                flash(f"{field_name}: {error}", "danger")
    return redirect(url_for("master_deposit.detail", karyawan_id=karyawan.id))


@master_deposit_bp.route("/sesuaikan-massal", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def sesuaikan_massal():
    form = SesuaikanSaldoMassalForm()
    daftar_saldo = DepositSaldo.query.join(Karyawan).order_by(Karyawan.nama).all()

    if form.validate_on_submit():
        perubahan = {}
        for saldo in daftar_saldo:
            nilai = request.form.get(f"saldo_{saldo.id}", "").strip()
            if not nilai:
                continue
            try:
                nominal = float(nilai.replace(",", "."))
            except ValueError:
                continue
            if nominal < 0:
                continue
            perubahan[saldo] = nominal

        if not perubahan:
            flash("Tidak ada saldo yang diubah.", "warning")
        else:
            jumlah = terapkan_sesuaikan_saldo_massal(perubahan, form.keterangan.data.strip())
            flash(f"Saldo deposit {jumlah} karyawan berhasil disesuaikan.", "success")
            return redirect(url_for("master_deposit.index"))

    return render_template("master_deposit/sesuaikan_massal.html", form=form, daftar_saldo=daftar_saldo)


@master_deposit_bp.route("/<int:karyawan_id>/transaksi/<int:transaksi_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_APPROVE)
def hapus_transaksi(karyawan_id, transaksi_id):
    karyawan = Karyawan.query.get_or_404(karyawan_id)
    transaksi = DepositTransaksi.query.get_or_404(transaksi_id)
    try:
        hapus_transaksi_deposit(transaksi)
        flash("Riwayat transaksi berhasil dihapus & saldo disesuaikan kembali.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("master_deposit.detail", karyawan_id=karyawan.id))


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

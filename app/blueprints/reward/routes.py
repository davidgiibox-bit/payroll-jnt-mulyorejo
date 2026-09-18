from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import PeriodePayroll, JenisReward, RewardEntry, EntertainmentEvent, Karyawan
from app.utils.akses import butuh_akses
from app.models.akses import LEVEL_LIHAT, LEVEL_EDIT
from app.blueprints.reward import reward_bp
from app.blueprints.reward.forms import (
    JenisRewardForm,
    UploadRewardForm,
    EntertainmentEventForm,
    TambahPesertaForm,
)
from app.services.import_service import parse_template_reward
from app.services.reward_service import hitung_ulang_reward_slip

KODE_MENU = "reward"


def _daftar_periode():
    return PeriodePayroll.query.order_by(PeriodePayroll.tahun.desc(), PeriodePayroll.bulan.desc()).all()


# --- Master Jenis Reward ---
@reward_bp.route("/jenis")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def jenis_index():
    form = JenisRewardForm()
    daftar_jenis = JenisReward.query.order_by(JenisReward.nama).all()
    return render_template("reward/jenis.html", daftar_jenis=daftar_jenis, form=form)


@reward_bp.route("/jenis/tambah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def jenis_tambah():
    form = JenisRewardForm()
    if form.validate_on_submit():
        if JenisReward.query.filter_by(nama=form.nama.data.strip()).first():
            flash("Jenis reward tersebut sudah ada.", "danger")
        else:
            db.session.add(JenisReward(nama=form.nama.data.strip()))
            db.session.commit()
            flash("Jenis reward berhasil ditambahkan.", "success")
    return redirect(url_for("reward.jenis_index"))


@reward_bp.route("/jenis/<int:jenis_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def jenis_hapus(jenis_id):
    jenis = JenisReward.query.get_or_404(jenis_id)
    db.session.delete(jenis)
    db.session.commit()
    flash("Jenis reward berhasil dihapus.", "success")
    return redirect(url_for("reward.jenis_index"))


# --- Upload Reward Biasa ---
@reward_bp.route("/")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def index():
    daftar_periode = _daftar_periode()
    form = UploadRewardForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

    periode_id_dipilih = request.args.get("periode_id", type=int)
    if periode_id_dipilih is None and daftar_periode:
        periode_id_dipilih = daftar_periode[0].id

    daftar_entry = []
    if periode_id_dipilih:
        daftar_entry = (
            RewardEntry.query.filter_by(periode_payroll_id=periode_id_dipilih, entertainment_event_id=None)
            .join(Karyawan)
            .order_by(Karyawan.nama)
            .all()
        )

    return render_template(
        "reward/index.html",
        form=form,
        daftar_periode=daftar_periode,
        periode_id_dipilih=periode_id_dipilih,
        daftar_entry=daftar_entry,
    )


@reward_bp.route("/unggah", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def unggah():
    daftar_periode = _daftar_periode()
    form = UploadRewardForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in daftar_periode]

    if not form.validate_on_submit():
        for field_name, error_list in form.errors.items():
            for error in error_list:
                flash(f"{field_name}: {error}", "danger")
        return redirect(url_for("reward.index"))

    periode = PeriodePayroll.query.get_or_404(form.periode_payroll_id.data)
    baris_valid, masalah = parse_template_reward(form.file.data)

    RewardEntry.query.filter_by(periode_payroll_id=periode.id, entertainment_event_id=None).delete()
    for karyawan, jenis_reward, nominal, keterangan in baris_valid:
        db.session.add(
            RewardEntry(
                periode_payroll_id=periode.id,
                karyawan_id=karyawan.id,
                jenis_reward_id=jenis_reward.id,
                nominal=nominal,
                keterangan=keterangan,
            )
        )
    db.session.flush()
    hitung_ulang_reward_slip(periode)

    flash(f"{len(baris_valid)} baris reward berhasil diunggah.", "success")
    if masalah:
        flash("Ada baris yang dilewati: " + "; ".join(masalah), "warning")
    return redirect(url_for("reward.index", periode_id=periode.id))


# --- Entertainment dengan Tim ---
@reward_bp.route("/entertainment")
@login_required
@butuh_akses(KODE_MENU, LEVEL_LIHAT)
def entertainment_index():
    daftar_periode = _daftar_periode()
    periode_id_dipilih = request.args.get("periode_id", type=int)
    if periode_id_dipilih is None and daftar_periode:
        periode_id_dipilih = daftar_periode[0].id

    daftar_event = []
    if periode_id_dipilih:
        daftar_event = EntertainmentEvent.query.filter_by(periode_payroll_id=periode_id_dipilih).all()

    return render_template(
        "reward/entertainment_index.html",
        daftar_periode=daftar_periode,
        periode_id_dipilih=periode_id_dipilih,
        daftar_event=daftar_event,
    )


@reward_bp.route("/entertainment/tambah", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def entertainment_tambah():
    form = EntertainmentEventForm()
    form.periode_payroll_id.choices = [(p.id, p.label) for p in _daftar_periode()]
    if form.validate_on_submit():
        event = EntertainmentEvent(
            periode_payroll_id=form.periode_payroll_id.data,
            deskripsi=form.deskripsi.data.strip(),
            total_biaya=form.total_biaya.data,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event entertainment berhasil dibuat. Tambahkan peserta di bawah.", "success")
        return redirect(url_for("reward.entertainment_detail", event_id=event.id))
    return render_template("reward/entertainment_form.html", form=form)


@reward_bp.route("/entertainment/<int:event_id>", methods=["GET", "POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def entertainment_detail(event_id):
    event = EntertainmentEvent.query.get_or_404(event_id)
    form = TambahPesertaForm()
    form.karyawan_id.choices = [(k.id, k.nama) for k in Karyawan.query.order_by(Karyawan.nama).all()]

    if form.validate_on_submit():
        db.session.add(
            RewardEntry(
                periode_payroll_id=event.periode_payroll_id,
                karyawan_id=form.karyawan_id.data,
                entertainment_event_id=event.id,
                nominal=form.nominal.data,
                keterangan=form.keterangan.data,
            )
        )
        db.session.flush()
        hitung_ulang_reward_slip(event.periode)
        flash("Peserta berhasil ditambahkan.", "success")
        return redirect(url_for("reward.entertainment_detail", event_id=event.id))

    total_teralokasi = sum((p.nominal for p in event.peserta_list), start=0)
    return render_template(
        "reward/entertainment_detail.html", event=event, form=form, total_teralokasi=total_teralokasi
    )


@reward_bp.route("/entertainment/<int:event_id>/peserta/<int:peserta_id>/hapus", methods=["POST"])
@login_required
@butuh_akses(KODE_MENU, LEVEL_EDIT)
def entertainment_hapus_peserta(event_id, peserta_id):
    event = EntertainmentEvent.query.get_or_404(event_id)
    peserta = RewardEntry.query.get_or_404(peserta_id)
    db.session.delete(peserta)
    db.session.flush()
    hitung_ulang_reward_slip(event.periode)
    flash("Peserta berhasil dihapus.", "success")
    return redirect(url_for("reward.entertainment_detail", event_id=event.id))

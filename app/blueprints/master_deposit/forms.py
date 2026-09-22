from flask_wtf import FlaskForm
from wtforms import DecimalField, StringField, SubmitField
from wtforms.validators import InputRequired, DataRequired, NumberRange


class PengaturanDepositForm(FlaskForm):
    default_potongan_bulanan = DecimalField(
        "Default Potongan Bulanan (Global)", validators=[InputRequired(), NumberRange(min=0)], places=2
    )
    default_limit_deposit = DecimalField(
        "Default Limit Deposit (Global)", validators=[InputRequired(), NumberRange(min=0)], places=2
    )
    submit = SubmitField("Simpan")


class SesuaikanSaldoForm(FlaskForm):
    saldo_baru = DecimalField("Saldo Baru", validators=[InputRequired(), NumberRange(min=0)], places=2)
    keterangan = StringField(
        "Keterangan (wajib, mis. 'Migrasi saldo dari pencatatan manual per Sep 2026')",
        validators=[DataRequired()],
    )
    submit = SubmitField("Simpan Penyesuaian")

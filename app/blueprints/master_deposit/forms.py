from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import InputRequired, NumberRange


class PengaturanDepositForm(FlaskForm):
    default_potongan_bulanan = DecimalField(
        "Default Potongan Bulanan (Global)", validators=[InputRequired(), NumberRange(min=0)], places=2
    )
    submit = SubmitField("Simpan")

from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, StringField, SubmitField
from wtforms.validators import InputRequired, Optional, NumberRange


class TunjanganJenjangForm(FlaskForm):
    min_bulan = IntegerField("Masa Kerja Minimal (bulan)", validators=[InputRequired(), NumberRange(min=0)])
    max_bulan = IntegerField(
        "Masa Kerja Maksimal (bulan, kosongkan utk tanpa batas)",
        validators=[Optional(), NumberRange(min=0)],
    )
    nominal = DecimalField("Nominal Tunjangan", validators=[InputRequired(), NumberRange(min=0)], places=2)
    keterangan = StringField("Keterangan", validators=[Optional()])
    submit = SubmitField("Simpan")

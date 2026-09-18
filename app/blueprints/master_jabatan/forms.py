from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, BooleanField, SubmitField
from wtforms.validators import DataRequired, InputRequired, NumberRange


class JabatanForm(FlaskForm):
    nama = StringField("Nama Jabatan", validators=[DataRequired()])
    gaji_pokok_default = DecimalField(
        "Gaji Pokok Default", validators=[InputRequired(), NumberRange(min=0)], places=2
    )
    kena_phl = BooleanField("Kena Potongan PHL")
    submit = SubmitField("Simpan")

from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, IntegerField, SubmitField
from wtforms.validators import InputRequired, NumberRange


class PilihPeriodeForm(FlaskForm):
    periode_payroll_id = SelectField("Periode", coerce=int, validators=[InputRequired()])
    submit = SubmitField("Tampilkan")


class TotalPHLForm(FlaskForm):
    total_biaya = DecimalField("Total Biaya PHL", validators=[InputRequired(), NumberRange(min=0)], places=2)
    total_paket = IntegerField("Total Paket Dihandle", validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField("Simpan")

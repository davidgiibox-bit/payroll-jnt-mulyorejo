from datetime import date
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import InputRequired

from app.models.periode_payroll import NAMA_BULAN

TAHUN_CHOICES = [(y, str(y)) for y in range(date.today().year - 1, date.today().year + 2)]
BULAN_CHOICES = [(i + 1, nama) for i, nama in enumerate(NAMA_BULAN)]


class PeriodePayrollForm(FlaskForm):
    tahun = SelectField("Tahun", choices=TAHUN_CHOICES, coerce=int, validators=[InputRequired()])
    bulan = SelectField("Bulan", choices=BULAN_CHOICES, coerce=int, validators=[InputRequired()])
    submit = SubmitField("Buat Periode")

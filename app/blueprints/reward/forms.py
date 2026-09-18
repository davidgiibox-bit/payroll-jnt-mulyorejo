from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Optional


class JenisRewardForm(FlaskForm):
    nama = StringField("Nama Jenis Reward", validators=[DataRequired()])
    submit = SubmitField("Tambah")


class UploadRewardForm(FlaskForm):
    periode_payroll_id = SelectField("Periode", coerce=int, validators=[InputRequired()])
    file = FileField(
        "File Template (.xlsx atau .csv)",
        validators=[FileRequired(), FileAllowed(["xlsx", "csv"], "Hanya file .xlsx atau .csv")],
    )
    submit = SubmitField("Unggah")


class EntertainmentEventForm(FlaskForm):
    periode_payroll_id = SelectField("Periode", coerce=int, validators=[InputRequired()])
    deskripsi = StringField("Deskripsi Event", validators=[DataRequired()])
    total_biaya = DecimalField("Total Biaya Event", validators=[InputRequired(), NumberRange(min=0)], places=2)
    submit = SubmitField("Buat Event")


class TambahPesertaForm(FlaskForm):
    karyawan_id = SelectField("Karyawan", coerce=int, validators=[InputRequired()])
    nominal = DecimalField("Nominal untuk Karyawan Ini", validators=[InputRequired(), NumberRange(min=0)], places=2)
    keterangan = StringField("Keterangan", validators=[Optional()])
    submit = SubmitField("Tambah Peserta")

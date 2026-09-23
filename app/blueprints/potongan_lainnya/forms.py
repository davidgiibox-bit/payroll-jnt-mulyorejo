from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired


class JenisPotonganLainnyaForm(FlaskForm):
    nama = StringField("Nama Jenis Potongan Lainnya", validators=[DataRequired()])
    submit = SubmitField("Tambah")


class UploadPotonganLainnyaForm(FlaskForm):
    periode_payroll_id = SelectField("Periode", coerce=int, validators=[InputRequired()])
    file = FileField(
        "File Template (.xlsx atau .csv)",
        validators=[FileRequired(), FileAllowed(["xlsx", "csv"], "Hanya file .xlsx atau .csv")],
    )
    submit = SubmitField("Unggah")

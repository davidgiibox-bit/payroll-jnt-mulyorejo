from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired


class JenisTambahanForm(FlaskForm):
    nama = StringField("Nama Jenis Tambahan", validators=[DataRequired()])
    submit = SubmitField("Tambah")


class UploadTambahanForm(FlaskForm):
    periode_payroll_id = SelectField("Periode", coerce=int, validators=[InputRequired()])
    file = FileField(
        "File Template (.xlsx atau .csv)",
        validators=[FileRequired(), FileAllowed(["xlsx", "csv"], "Hanya file .xlsx atau .csv")],
    )
    submit = SubmitField("Unggah")

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, InputRequired, NumberRange


class ReasonClaimForm(FlaskForm):
    nama = StringField("Nama Alasan", validators=[DataRequired()])
    submit = SubmitField("Tambah")


class UploadFileForm(FlaskForm):
    file = FileField(
        "File Template (.xlsx atau .csv)",
        validators=[FileRequired(), FileAllowed(["xlsx", "csv"], "Hanya file .xlsx atau .csv")],
    )
    submit = SubmitField("Unggah")


class AssignKasusForm(FlaskForm):
    karyawan_id = SelectField("Karyawan Bertanggung Jawab", coerce=int, validators=[InputRequired()])
    reason_claim_id = SelectField("Reason Claim", coerce=int, validators=[InputRequired()])
    submit = SubmitField("Simpan Assignment")


class KeputusanForm(FlaskForm):
    keputusan = SelectField(
        "Keputusan", choices=[("langsung", "Potong Langsung Penuh"), ("cicil", "Cicil")]
    )
    jumlah_bulan = IntegerField("Jumlah Bulan Cicilan", validators=[NumberRange(min=1)], default=3)
    submit = SubmitField("Simpan")

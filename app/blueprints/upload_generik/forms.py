from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, SubmitField
from wtforms.validators import InputRequired


class UploadKomponenForm(FlaskForm):
    periode_payroll_id = SelectField("Periode", coerce=int, validators=[InputRequired()])
    file = FileField(
        "File Template (.xlsx atau .csv)",
        validators=[FileRequired(), FileAllowed(["xlsx", "csv"], "Hanya file .xlsx atau .csv")],
    )
    submit = SubmitField("Unggah")

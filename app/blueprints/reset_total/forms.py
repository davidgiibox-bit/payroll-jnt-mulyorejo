from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, AnyOf

FRASA_KONFIRMASI = "HAPUS SEMUA DATA"


class ResetTotalForm(FlaskForm):
    konfirmasi = StringField(
        f"Ketik persis \"{FRASA_KONFIRMASI}\" untuk konfirmasi",
        validators=[DataRequired(), AnyOf([FRASA_KONFIRMASI], message="Teks konfirmasi tidak cocok.")],
    )
    submit = SubmitField("Ya, Hapus SEMUA Data Sekarang")

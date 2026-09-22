from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    DecimalField,
    BooleanField,
    DateField,
    TextAreaField,
    SubmitField,
)
from wtforms.validators import DataRequired, InputRequired, Optional, NumberRange, Length

STATUS_PAJAK_CHOICES = [
    ("TK/0", "TK/0"), ("TK/1", "TK/1"), ("TK/2", "TK/2"), ("TK/3", "TK/3"),
    ("K/0", "K/0"), ("K/1", "K/1"), ("K/2", "K/2"), ("K/3", "K/3"),
]

JENIS_KELAMIN_CHOICES = [("L", "Laki-laki"), ("P", "Perempuan")]


class KaryawanForm(FlaskForm):
    kode_dp = StringField("Kode DP", validators=[DataRequired(), Length(max=20)])
    nik_karyawan = StringField("NIK Karyawan", validators=[DataRequired(), Length(max=30)])
    nama = StringField("Nama", validators=[DataRequired(), Length(max=150)])
    jabatan_id = SelectField("Jabatan", coerce=int, validators=[DataRequired()])

    npwp = StringField("NPWP", validators=[Optional(), Length(max=30)])
    nik_ktp = StringField("NIK KTP", validators=[Optional(), Length(max=30)])
    rekening_bank = StringField("Rekening Bank", validators=[Optional(), Length(max=100)])
    alamat_npwp = TextAreaField("Alamat NPWP", validators=[Optional()])

    status_pajak = SelectField("Status Pajak", choices=STATUS_PAJAK_CHOICES, validators=[Optional()])
    jenis_kelamin = SelectField("Jenis Kelamin", choices=JENIS_KELAMIN_CHOICES, validators=[Optional()])

    tanggal_join = DateField("Tanggal Join", validators=[DataRequired()])
    tanggal_resign = DateField("Tanggal Resign", validators=[Optional()])
    status_aktif = BooleanField("Aktif", default=True)

    limit_deposit_individual = DecimalField(
        "Limit Deposit Individual (kosongkan utk pakai default global)",
        validators=[Optional(), NumberRange(min=0)],
        places=2,
    )
    potongan_bpjs_tk = DecimalField(
        "Potongan BPJS-TK", validators=[InputRequired(), NumberRange(min=0)], places=2, default=0
    )
    tunjangan_masa_kerja = DecimalField(
        "Tunjangan Masa Kerja", validators=[InputRequired(), NumberRange(min=0)], places=2, default=0
    )

    submit = SubmitField("Simpan")

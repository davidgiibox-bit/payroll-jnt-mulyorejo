from app.extensions import db

LEVEL_TIDAK_ADA = "tidak_ada"
LEVEL_LIHAT = "lihat"
LEVEL_EDIT = "edit"
LEVEL_APPROVE = "approve"

LEVEL_CHOICES = [LEVEL_TIDAK_ADA, LEVEL_LIHAT, LEVEL_EDIT, LEVEL_APPROVE]


class Menu(db.Model):
    """Daftar menu/modul sistem — dipakai sebagai kolom pada matriks Jabatan x Menu."""

    __tablename__ = "menu"

    id = db.Column(db.Integer, primary_key=True)
    kode_menu = db.Column(db.String(50), nullable=False, unique=True)
    nama_menu = db.Column(db.String(100), nullable=False)
    urutan = db.Column(db.Integer, nullable=False, default=0)

    hak_akses_list = db.relationship("HakAkses", back_populates="menu", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Menu {self.kode_menu}>"


class HakAkses(db.Model):
    """Matriks Jabatan x Menu, tiap kombinasi punya 1 level akses:
    tidak_ada / lihat / edit / approve."""

    __tablename__ = "hak_akses"
    __table_args__ = (db.UniqueConstraint("jabatan_id", "menu_id", name="uq_hak_akses_jabatan_menu"),)

    id = db.Column(db.Integer, primary_key=True)

    jabatan_id = db.Column(db.Integer, db.ForeignKey("jabatan.id"), nullable=False)
    jabatan = db.relationship("Jabatan", back_populates="hak_akses_list")

    menu_id = db.Column(db.Integer, db.ForeignKey("menu.id"), nullable=False)
    menu = db.relationship("Menu", back_populates="hak_akses_list")

    level_akses = db.Column(db.String(20), nullable=False, default=LEVEL_TIDAK_ADA)

    def __repr__(self):
        return f"<HakAkses jabatan={self.jabatan_id} menu={self.menu_id} level={self.level_akses}>"

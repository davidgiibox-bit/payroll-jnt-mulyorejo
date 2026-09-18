import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-ganti-di-production")

    database_url = os.environ.get("DATABASE_URL", "")
    # Render kadang kasih url dengan skema postgres:// atau postgresql://
    # — driver yang dipakai di sini adalah psycopg (v3), jadi perlu skema postgresql+psycopg://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///" + os.path.join(basedir, "payroll_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

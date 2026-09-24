"""Sinkronkan sequence id jenis_potongan_lainnya (Postgres)

Migrasi sebelumnya (f5652c3ab675) memasukkan jenis awal dengan id eksplisit 1-5, sehingga
sequence auto-increment di PostgreSQL masih di 1 dan menambah jenis baru lewat halaman
master akan bentrok (duplicate key). Migrasi ini menyamakan sequence dengan id terbesar.
Tidak berpengaruh di SQLite (auto-increment-nya mengikuti id terbesar sendiri).

Revision ID: a7c1d9e04b52
Revises: f5652c3ab675
Create Date: 2026-09-24 10:00:00.000000

"""
from alembic import op


revision = 'a7c1d9e04b52'
down_revision = 'f5652c3ab675'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(
            "SELECT setval(pg_get_serial_sequence('jenis_potongan_lainnya', 'id'), "
            "COALESCE((SELECT MAX(id) FROM jenis_potongan_lainnya), 1))"
        )


def downgrade():
    pass

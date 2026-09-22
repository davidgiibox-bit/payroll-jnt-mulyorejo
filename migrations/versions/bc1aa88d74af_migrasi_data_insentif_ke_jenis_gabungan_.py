"""Migrasi data insentif ke jenis gabungan dan bersihkan menu lama

Revision ID: bc1aa88d74af
Revises: d1f2df00e572
Create Date: 2026-09-22 14:56:36.000110

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc1aa88d74af'
down_revision = 'd1f2df00e572'
branch_labels = None
depends_on = None


def upgrade():
    # Gabungkan data lama (3 jenis insentif terpisah) jadi 1 jenis 'insentif'
    op.execute(
        "UPDATE komponen_upload SET jenis = 'insentif' "
        "WHERE jenis IN ('insentif_bo_dp', 'insentif_sprinter', 'insentif_kurir')"
    )

    # Bersihkan 3 menu lama (dan hak akses terkait) yang sudah tidak dipakai
    op.execute(
        "DELETE FROM hak_akses WHERE menu_id IN ("
        "SELECT id FROM menu WHERE kode_menu IN "
        "('upload_insentif_bo_dp', 'upload_insentif_sprinter', 'upload_insentif_kurir'))"
    )
    op.execute(
        "DELETE FROM menu WHERE kode_menu IN "
        "('upload_insentif_bo_dp', 'upload_insentif_sprinter', 'upload_insentif_kurir')"
    )


def downgrade():
    pass

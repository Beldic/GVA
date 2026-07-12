"""perfil público del organizador (web + logo) y retrato del autor

Para la ficha de exposición: usuario gana web/logo_public_id/logo_url
(logo subible a Cloudinary; la convención de archivo en static sigue de
respaldo) y autor gana foto_public_id (retrato subido, además de la URL
manual foto_url que ya existía).

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-07-12

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuario", schema=None) as batch_op:
        batch_op.add_column(sa.Column("web", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("logo_public_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("logo_url", sa.String(length=500), nullable=True))
    with op.batch_alter_table("autor", schema=None) as batch_op:
        batch_op.add_column(sa.Column("foto_public_id", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("autor", schema=None) as batch_op:
        batch_op.drop_column("foto_public_id")
    with op.batch_alter_table("usuario", schema=None) as batch_op:
        batch_op.drop_column("logo_url")
        batch_op.drop_column("logo_public_id")
        batch_op.drop_column("web")
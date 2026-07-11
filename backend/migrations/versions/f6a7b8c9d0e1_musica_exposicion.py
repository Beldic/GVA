"""exposicion: hilo musical opcional (musica_public_id + musica_url)

El organizador puede subir una pista de audio (Cloudinary, resource_type
video) que suena en bucle durante el recorrido 3D, con control de silencio
en el HUD del visor.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-11

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("musica_public_id", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("musica_url", sa.String(length=500), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_column("musica_url")
        batch_op.drop_column("musica_public_id")

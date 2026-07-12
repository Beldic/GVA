"""exposicion: vídeo de presentación (video_url)

Enlace a YouTube/Vimeo (embebido en modo privacidad, sin cookies) o a un
mp4 directo. Se muestra en la ficha de la exposición, en formato compacto.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(sa.Column("video_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_column("video_url")

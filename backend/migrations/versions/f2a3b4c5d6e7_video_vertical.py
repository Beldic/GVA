"""exposicion: orientación del vídeo de presentación (video_vertical)

True si el vídeo es 9:16 (grabado con móvil): la ficha lo muestra en un
marco vertical compacto en vez del 16:9. Se detecta al guardar el enlace
(Shorts de YouTube por la URL; el resto vía oEmbed, best-effort).

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(sa.Column("video_vertical", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_column("video_vertical")

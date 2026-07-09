"""exposicion: cierre manual del organizador (cerrada_manual)

El estado de apertura de cara al visitante (`Exposicion.apertura`) combina
este flag con las fechas de la exposición: cerrada a mano o fuera de fechas
-> «cerrada»; antes de fecha_inicio -> «próximamente»; si no -> «abierta».

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-09

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "cerrada_manual",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("exposicion", schema=None) as batch_op:
        batch_op.drop_column("cerrada_manual")

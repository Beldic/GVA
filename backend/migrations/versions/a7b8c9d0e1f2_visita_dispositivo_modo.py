"""visita: dimensiones anónimas de la visita (dispositivo + modo)

dispositivo (movil/escritorio, del user-agent) y modo (3d/2d) del primer
acceso de la sesión. Sin identidad del visitante: solo agregados para las
estadísticas del panel del organizador. Las visitas previas quedan NULL.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-12

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("visita", schema=None) as batch_op:
        batch_op.add_column(sa.Column("dispositivo", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("modo", sa.String(length=10), nullable=True))


def downgrade():
    with op.batch_alter_table("visita", schema=None) as batch_op:
        batch_op.drop_column("modo")
        batch_op.drop_column("dispositivo")

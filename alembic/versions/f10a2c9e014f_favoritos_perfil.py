"""Quatro albuns publicos do perfil, independentes da biblioteca.

Revision ID: f10a2c9e014f
Revises: d85c2b9e014f
"""
from alembic import op
import sqlalchemy as sa

revision = "f10a2c9e014f"
down_revision = "d85c2b9e014f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "favoritos_perfil",
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("posicao", sa.Integer(), nullable=False),
        sa.Column("obra_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("usuario_id", "posicao"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["obra_id"], ["obras.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("usuario_id", "obra_id", name="uq_favoritos_perfil_obra"),
        sa.CheckConstraint("posicao BETWEEN 1 AND 4", name="ck_favoritos_perfil_posicao"),
    )


def downgrade():
    op.drop_table("favoritos_perfil")

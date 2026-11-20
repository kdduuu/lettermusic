"""Adiciona revogacao de sessoes por usuario.

Revision ID: c48a129f0e85
Revises: b85e3a7c1f02
"""
from alembic import op
import sqlalchemy as sa

revision = "c48a129f0e85"
down_revision = "b85e3a7c1f02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column(
            "sessao_versao",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade():
    op.drop_column("usuarios", "sessao_versao")

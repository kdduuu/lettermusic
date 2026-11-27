"""Contadores persistentes de limitacao de requisicoes."""

from alembic import op
import sqlalchemy as sa

revision = "f11a1c9e014f"
down_revision = "f10a2c9e014f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "limites_requisicoes",
        sa.Column("chave", sa.String(64), primary_key=True),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("expira_em", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("quantidade > 0", name="ck_limites_requisicoes_quantidade"),
    )
    op.create_index(
        "ix_limites_requisicoes_expira_em",
        "limites_requisicoes",
        ["expira_em"],
    )


def downgrade():
    op.drop_index("ix_limites_requisicoes_expira_em", table_name="limites_requisicoes")
    op.drop_table("limites_requisicoes")

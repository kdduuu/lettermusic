"""Recuperacao de senha e verificacao de email.

Revision ID: d85c2b9e014f
Revises: c48a129f0e85
"""
from alembic import op
import sqlalchemy as sa

revision = "d85c2b9e014f"
down_revision = "c48a129f0e85"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column(
            "email_confirmado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "tokens_conta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("finalidade", sa.String(20), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "expira_em", sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "usado_em", sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token_hash"),
    )

    op.create_index(
        "ix_tokens_conta_usuario_id",
        "tokens_conta",
        ["usuario_id"],
    )


def downgrade():
    op.drop_index(
        "ix_tokens_conta_usuario_id",
        table_name="tokens_conta",
    )
    op.drop_table("tokens_conta")
    op.drop_column("usuarios", "email_confirmado")

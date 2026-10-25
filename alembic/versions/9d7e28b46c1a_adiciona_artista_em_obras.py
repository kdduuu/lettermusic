"""Adiciona o artista ao catalogo musical.

Revision ID: 9d7e28b46c1a
Revises: 5f86c427a41b
"""

from alembic import op
import sqlalchemy as sa

revision = "9d7e28b46c1a"
down_revision = "5f86c427a41b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable para preservar obras ja cadastradas sem artista.
    op.add_column("obras", sa.Column("artista", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("obras", "artista")

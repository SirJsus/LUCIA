"""agrega alternatives_json a analyzed_moves

Revision ID: 7a1c4e9d2b30
Revises: 3665445db37f
Create Date: 2026-09-08 13:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a1c4e9d2b30"
down_revision: str | Sequence[str] | None = "3665445db37f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nullable a propósito: los análisis anteriores a RF-10 no tienen
    # alternativas guardadas, y `None` los distingue de "el motor no propuso
    # ninguna". Para esos, el router las recupera de `position_cache` si
    # siguen ahí; si no, el visor enseña una sola flecha como hasta ahora.
    op.add_column(
        "analyzed_moves",
        sa.Column("alternatives_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analyzed_moves", "alternatives_json")

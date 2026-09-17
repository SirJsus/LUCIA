"""agrega cache del opening explorer

Revision ID: b4e8c17f0a92
Revises: 9c2d51ab7e04
Create Date: 2026-09-10 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e8c17f0a92"
down_revision: str | Sequence[str] | None = "9c2d51ab7e04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Sin datos que rellenar: se llena preguntando a Lichess, y hasta que se
    # pregunte la comparación de repertorio (RF-3.6) simplemente no tiene qué
    # enseñar. La tabla se puede vaciar entera sin perder nada propio.
    op.create_table(
        "explorer_positions",
        sa.Column("epd", sa.String(), nullable=False),
        sa.Column("masters_json", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("epd"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("explorer_positions")

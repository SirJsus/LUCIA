"""agrega sparring_games (partidas contra el motor calibrado)

Revision ID: f3d9a1c47b58
Revises: e1a7c93d40b2
Create Date: 2026-09-21 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3d9a1c47b58"
down_revision: str | Sequence[str] | None = "e1a7c93d40b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tabla aparte de `games` a propósito: una partida de sparring no cuenta en
    # estadísticas ni en patrones (RF-3), igual que un tablero sin publicar
    # (RF-6.5). Ver la docstring de `SparringGame` en db/models.py.
    op.create_table(
        "sparring_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_color", sa.String(), nullable=False),
        sa.Column("engine", sa.String(), nullable=False),
        # Nulo en Lc0: su fuerza es la de la red Maia que se cargó, no un
        # número que se le pueda pedir por UCI.
        sa.Column("engine_elo", sa.Integer(), nullable=True),
        sa.Column("starting_fen", sa.String(), nullable=False),
        sa.Column("moves_uci_json", sa.JSON(), nullable=False),
        # Nulos mientras la partida sigue viva: `result` es la única marca de
        # que terminó.
        sa.Column("result", sa.String(), nullable=True),
        sa.Column("termination", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("sparring_games")

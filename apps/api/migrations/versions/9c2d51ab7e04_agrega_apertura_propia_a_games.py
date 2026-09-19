"""agrega apertura propia a games

Revision ID: 9c2d51ab7e04
Revises: 7a1c4e9d2b30
Create Date: 2026-09-09 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from lucia_core.openings import opening_of_pgn

# revision identifiers, used by Alembic.
revision: str = "9c2d51ab7e04"
down_revision: str | Sequence[str] | None = "7a1c4e9d2b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("games", sa.Column("opening_eco", sa.String(), nullable=True))
    op.add_column("games", sa.Column("opening_name", sa.String(), nullable=True))

    # Las partidas ya importadas no se vuelven a descargar para esto: la
    # apertura sale de su PGN, que ya está en la base. Es la misma idea que en
    # ADR-0008 —deducir de lo guardado en vez de repetir el trabajo—, con la
    # diferencia de que aquí sí se persiste: agrupar por apertura en SQL lo
    # necesita, y el resultado no depende de ningún umbral ajustable.
    games = sa.table(
        "games",
        sa.column("id", sa.Integer),
        sa.column("pgn", sa.String),
        sa.column("opening_eco", sa.String),
        sa.column("opening_name", sa.String),
    )
    connection = op.get_bind()
    for game_id, pgn in connection.execute(sa.select(games.c.id, games.c.pgn)):
        opening = opening_of_pgn(pgn)
        if opening is None:
            continue
        connection.execute(
            games.update()
            .where(games.c.id == game_id)
            .values(opening_eco=opening.eco, opening_name=opening.name)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("games", "opening_name")
    op.drop_column("games", "opening_eco")

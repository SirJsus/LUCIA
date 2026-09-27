"""sparring que retoma una partida propia (re-juega desde el error)

Revision ID: d5a81c6e3f04
Revises: c7b2e9f05a31
Create Date: 2026-09-21 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5a81c6e3f04"
down_revision: str | Sequence[str] | None = "c7b2e9f05a31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Procedencia, no dependencia: de qué partida propia y de qué jugada se
    # retomó esta (RF-4.4). Nulas en las partidas de sparring que empiezan
    # desde el principio, que son las que ya había.
    #
    # `batch_alter_table` porque SQLite no sabe añadir una clave foránea con
    # un ALTER: recrea la tabla y copia las filas.
    with op.batch_alter_table("sparring_games") as batch:
        batch.add_column(sa.Column("origin_game_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("origin_ply", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_sparring_games_origin_game_id_games",
            "games",
            ["origin_game_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("sparring_games") as batch:
        batch.drop_constraint("fk_sparring_games_origin_game_id_games", type_="foreignkey")
        batch.drop_column("origin_ply")
        batch.drop_column("origin_game_id")

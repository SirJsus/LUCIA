"""opening_drills: la baraja se llama source y las partidas games_played

Revision ID: e6c4d20b7f19
Revises: d5a81c6e3f04
Create Date: 2026-09-23 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6c4d20b7f19"
down_revision: str | Sequence[str] | None = "d5a81c6e3f04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Solo cambian los nombres; los datos se quedan donde están.
    #
    # `reason` decía "motivo" en una tabla donde el motivo ya lo cuentan
    # `games_played` y `score_percent`: lo que guarda es **de qué baraja salió**
    # la línea ("departure" u "opening"), y eso es su procedencia. `games` no
    # decía qué se contaba —la tabla no guarda partidas—, sino cuántas partidas
    # propias justifican el drill.
    #
    # `batch_alter_table` porque SQLite no sabe renombrar una columna con un
    # ALTER a secas: recrea la tabla y copia las filas, conservando el índice
    # de `due_at` y la clave única `(player_color, line_uci)`.
    with op.batch_alter_table("opening_drills") as batch:
        batch.alter_column("reason", new_column_name="source", existing_type=sa.String())
        batch.alter_column("games", new_column_name="games_played", existing_type=sa.Integer())


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("opening_drills") as batch:
        batch.alter_column("games_played", new_column_name="games", existing_type=sa.Integer())
        batch.alter_column("source", new_column_name="reason", existing_type=sa.String())

"""tablero propio publicado como partida

Marcar un tablero como "partida propia" (RF-6.5) deja de ser un booleano
suelto y pasa a ser un enlace: `boards.own_game_id` apunta a la fila de
`games` en la que el tablero se publicó, que es lo que hace que el dashboard,
los filtros y los patrones lo cuenten sin que ninguna consulta de RF-3 tenga
que aprender qué es un tablero (ADR-0014).

El booleano `is_own_game` se va porque sería una segunda versión de la misma
verdad. **Las marcas que ya existieran se pierden**: un tablero marcado con el
esquema anterior no trae rival, resultado ni fecha, y publicarlo obligaría a
inventarlos. Hay que volver a marcarlo desde la pantalla del tablero, que ya
pide esos datos.

Va en `batch_alter_table` porque SQLite no sabe añadir una clave foránea ni
quitar una columna sin recrear la tabla.

Revision ID: a71c40f5d3e8
Revises: 5ce9943fe2dc
Create Date: 2026-09-18 18:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a71c40f5d3e8"
down_revision: str | Sequence[str] | None = "5ce9943fe2dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("boards") as batch:
        batch.add_column(sa.Column("own_game_id", sa.Integer(), nullable=True))
        # Con nombre explícito: SQLite recrea la tabla para esto, y sin
        # nombre no habría forma de quitarla en el `downgrade`.
        batch.create_foreign_key(
            "fk_boards_own_game_id_games", "games", ["own_game_id"], ["id"], ondelete="SET NULL"
        )
        batch.drop_column("is_own_game")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("boards") as batch:
        batch.add_column(
            sa.Column("is_own_game", sa.Boolean(), nullable=False, server_default=sa.false())
        )
    # La marca se recupera del enlace antes de tirarlo. La partida publicada
    # se queda en el historial: el esquema anterior no sabe que salió de un
    # tablero, así que allí se ve como una partida importada más.
    op.execute(sa.text("UPDATE boards SET is_own_game = 1 WHERE own_game_id IS NOT NULL"))
    with op.batch_alter_table("boards") as batch:
        batch.drop_constraint("fk_boards_own_game_id_games", type_="foreignkey")
        batch.drop_column("own_game_id")

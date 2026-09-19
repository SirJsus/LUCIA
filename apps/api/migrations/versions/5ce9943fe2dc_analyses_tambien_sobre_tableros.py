"""analyses tambien sobre tableros

Un análisis puede colgar ahora de una partida (`game_id`, RF-2) o de un
tablero de análisis (`board_id`, RF-6.9), nunca de las dos: son la misma
corrida de motor sobre las mismas jugadas, así que comparten tabla en vez de
duplicar `analyzed_moves` y todo lo que lee de ella.

Va en `batch_alter_table` porque SQLite no sabe cambiar la nulabilidad de una
columna ni añadir una clave foránea después de crear la tabla: alembic la
recrea, copia las filas y la renombra. Las filas que ya existen son todas de
partidas, así que se quedan con `board_id` y `analyzed_pgn` en nulo sin tocarlas.

Revision ID: 5ce9943fe2dc
Revises: 97d2b0821d2b
Create Date: 2026-09-18 13:38:30.922817

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ce9943fe2dc"
down_revision: str | Sequence[str] | None = "97d2b0821d2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("analyses") as batch:
        batch.add_column(sa.Column("board_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("analyzed_pgn", sa.String(), nullable=True))
        batch.alter_column("game_id", existing_type=sa.INTEGER(), nullable=True)
        # Con nombre explícito: SQLite recrea la tabla para esto, y sin
        # nombre no habría forma de quitarla en el `downgrade`.
        batch.create_foreign_key(
            "fk_analyses_board_id_boards", "boards", ["board_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Los análisis de tablero no caben en el esquema anterior —`game_id` pasa
    # a ser obligatorio— así que se borran antes de estrechar la columna.
    op.execute(
        sa.text(
            "DELETE FROM analyzed_moves WHERE analysis_id IN "
            "(SELECT id FROM analyses WHERE game_id IS NULL)"
        )
    )
    op.execute(sa.text("DELETE FROM analyses WHERE game_id IS NULL"))
    with op.batch_alter_table("analyses") as batch:
        batch.drop_constraint("fk_analyses_board_id_boards", type_="foreignkey")
        batch.alter_column("game_id", existing_type=sa.INTEGER(), nullable=False)
        batch.drop_column("analyzed_pgn")
        batch.drop_column("board_id")

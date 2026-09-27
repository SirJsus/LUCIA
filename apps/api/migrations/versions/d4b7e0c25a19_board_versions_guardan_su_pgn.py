"""board_versions guardan su pgn

Cada versión del historial de un tablero (RF-6.8) guarda ahora también su PGN,
tal como lo compuso el front (`tree.ts::toPgn`). Lo pide RF-6.5: un tablero
publicado como partida propia tiene que poner al día su fila de `games` al
deshacer o rehacer, y la API no sabe recorrer el árbol para componer ese PGN.
Con la columna, deshacer lo resuelve el servidor en la misma petición en vez de
pedirle a la pantalla que vuelva a publicar el tablero.

Las filas que ya existen quedan con `pgn` en nulo: no se sabe cómo quedó su
árbol en PGN e inventarlo sería peor. Deshacer hasta una de ellas desenlaza el
análisis —deja de contar en las estadísticas— hasta el siguiente guardado, que
es lo que hacía todo el historial antes de esta columna.

Revision ID: d4b7e0c25a19
Revises: c8f3a2b91e47
Create Date: 2026-09-18 19:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4b7e0c25a19"
down_revision: str | Sequence[str] | None = "c8f3a2b91e47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("board_versions", sa.Column("pgn", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("board_versions", "pgn")

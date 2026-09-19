"""analyzed_moves se van con su analisis

`analyzed_moves.analysis_id` pasa a tener `ON DELETE CASCADE`. Hasta ahora esa
limpieza la hacía solo la relación de SQLAlchemy, que basta cuando el análisis
se borra desde el ORM pero no cuando lo borra la propia base: borrar un tablero
se lleva sus `analyses` por la clave foránea (ADR-0013) sin cargarlos, y las
jugadas de esos análisis se quedaban apuntando a una fila que ya no existe.

Esto no se notaba porque sqlite trae las claves foráneas apagadas por conexión;
desde que `db/base.py::create_db_engine` enciende `PRAGMA foreign_keys=ON`, el
borrado del tablero falla en vez de dejar basura, que es lo que había que
arreglar.

Va en `batch_alter_table` porque SQLite no sabe cambiar una clave foránea sin
recrear la tabla.

Revision ID: c8f3a2b91e47
Revises: a71c40f5d3e8
Create Date: 2026-09-18 19:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8f3a2b91e47"
down_revision: str | Sequence[str] | None = "a71c40f5d3e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Las que ya quedaron huérfanas con el pragma apagado no caben en el
    # esquema nuevo: se van antes de declarar la restricción.
    op.execute(
        sa.text("DELETE FROM analyzed_moves WHERE analysis_id NOT IN (SELECT id FROM analyses)")
    )
    with op.batch_alter_table("analyzed_moves") as batch:
        batch.create_foreign_key(
            "fk_analyzed_moves_analysis_id_analyses",
            "analyses",
            ["analysis_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("analyzed_moves") as batch:
        batch.drop_constraint("fk_analyzed_moves_analysis_id_analyses", type_="foreignkey")
        batch.create_foreign_key(
            "fk_analyzed_moves_analysis_id_analyses", "analyses", ["analysis_id"], ["id"]
        )

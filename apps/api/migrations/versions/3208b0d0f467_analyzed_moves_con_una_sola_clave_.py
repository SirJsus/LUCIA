"""analyzed_moves con una sola clave foranea

`analyzed_moves.analysis_id` tenía **dos** claves foráneas hacia `analyses.id`:
la original sin nombre, con `ON DELETE NO ACTION`, y la que añadió la migración
`c8f3a2b91e47` con `ON DELETE CASCADE`. Aquella no quitó la primera: dentro de
un `batch_alter_table`, alembic reconstruye la tabla a partir de lo que refleja
de la base, así que reflejó la original, la volvió a crear y le añadió la nueva
al lado.

**No era un fallo vivo** —se comprobó sobre una copia de la base el 2026-09-19:
sqlite aplica la cascada y la restricción `NO ACTION` ya no encuentra huérfanas
que objetar, así que borrar un análisis con sus jugadas funcionaba—. Lo que
dejaba era un esquema que dice dos cosas contradictorias sobre la misma
columna, un `SAWarning` en cada `alembic check` ("SQL-parsed foreign key
constraint could not be located in PRAGMA foreign_keys") y una trampa para la
próxima migración que toque esta tabla, que habría arrastrado el par otra vez.

**Por qué esta sí quita la de más y `c8f3a2b91e47` no**: aquí el
`batch_alter_table` lleva `copy_from`, que le da a alembic la definición exacta
de la tabla en vez de dejarle reflejarla. Con eso la reconstruye desde lo que
dice este archivo —una sola clave foránea, la del cascade— y la sobrante
desaparece. `recreate="always"` es lo que fuerza la reconstrucción aunque no se
le pida ningún cambio de columna.

La definición se escribe aquí entera y no se importa de `db/models.py` a
propósito: una migración describe la tabla **tal como era en este punto de la
historia**, y si importara el modelo cambiaría de significado cada vez que el
modelo cambie.

Revision ID: 3208b0d0f467
Revises: d4b7e0c25a19
Create Date: 2026-09-19 12:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3208b0d0f467"
down_revision: str | Sequence[str] | None = "d4b7e0c25a19"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CASCADE_CONSTRAINT_NAME = "fk_analyzed_moves_analysis_id_analyses"


def _analyzed_moves_table(*, with_cascade: bool) -> sa.Table:
    """La tabla tal como debe quedar, para que alembic la reconstruya desde
    aquí en vez de desde lo que refleje de la base.

    `with_cascade` es lo único que cambia entre subir y bajar: la misma tabla
    con la clave foránea que borra en cascada o con la que no hace nada.
    """
    return sa.Table(
        "analyzed_moves",
        sa.MetaData(),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("ply", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(), nullable=False),
        sa.Column("san", sa.String(), nullable=False),
        sa.Column("uci", sa.String(), nullable=False),
        sa.Column("fen_before", sa.String(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("move_accuracy", sa.Float(), nullable=False),
        sa.Column("win_percent_before", sa.Float(), nullable=False),
        sa.Column("win_percent_after", sa.Float(), nullable=False),
        sa.Column("best_move_uci", sa.String(), nullable=True),
        sa.Column("phase", sa.String(), server_default="middlegame", nullable=False),
        sa.Column("alternatives_json", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name=CASCADE_CONSTRAINT_NAME,
            ondelete="CASCADE" if with_cascade else None,
        ),
    )


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table(
        "analyzed_moves",
        copy_from=_analyzed_moves_table(with_cascade=True),
        recreate="always",
    ):
        pass


def downgrade() -> None:
    """Downgrade schema.

    No se restaura el par de claves foráneas —era el error— sino el estado que
    `c8f3a2b91e47` quería dejar: una sola, sin cascada.
    """
    with op.batch_alter_table(
        "analyzed_moves",
        copy_from=_analyzed_moves_table(with_cascade=False),
        recreate="always",
    ):
        pass

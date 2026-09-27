"""agrega puzzles (entrenamiento desde los errores propios)

Revision ID: e1a7c93d40b2
Revises: 3208b0d0f467
Create Date: 2026-09-19 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a7c93d40b2"
down_revision: str | Sequence[str] | None = "3208b0d0f467"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nace vacía: los puzzles se generan desde los análisis que ya hay
    # (RF-4.1), con el botón de la pantalla de Entrenamiento, y no al migrar.
    # Generar aquí obligaría a la migración a saber de motores, de colores y
    # de quién es el usuario, que es justo lo que decide `services/training.py`.
    op.create_table(
        "puzzles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("ply", sa.Integer(), nullable=False),
        sa.Column("fen", sa.String(), nullable=False),
        sa.Column("played_uci", sa.String(), nullable=False),
        sa.Column("solutions_json", sa.JSON(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("win_percent_before", sa.Float(), nullable=False),
        sa.Column("win_percent_after", sa.Float(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("ease_factor", sa.Float(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_id", "ply", name="uq_puzzle_game_ply"),
    )
    # La cola de repaso se pide siempre igual —"lo que vence hasta ahora, lo
    # más atrasado primero"—, así que el índice es por esa columna.
    op.create_index("ix_puzzles_due_at", "puzzles", ["due_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_puzzles_due_at", table_name="puzzles")
    op.drop_table("puzzles")

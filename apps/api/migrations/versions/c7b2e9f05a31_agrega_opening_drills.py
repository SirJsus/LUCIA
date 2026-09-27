"""agrega opening_drills (drill de aperturas)

Revision ID: c7b2e9f05a31
Revises: f3d9a1c47b58
Create Date: 2026-09-21 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7b2e9f05a31"
down_revision: str | Sequence[str] | None = "f3d9a1c47b58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nace vacía: los drills se generan con el botón de la pantalla de
    # Entrenamiento, a partir del repertorio ya comparado (RF-3.6) y de las
    # estadísticas por apertura (RF-3.2). Generarlos aquí obligaría a la
    # migración a saber de teoría de maestros y de quién es el usuario, que es
    # lo que decide `services/drills.py`.
    op.create_table(
        "opening_drills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("player_color", sa.String(), nullable=False),
        sa.Column("line_uci", sa.String(), nullable=False),
        sa.Column("opening_eco", sa.String(), nullable=True),
        sa.Column("opening_name", sa.String(), nullable=True),
        sa.Column("games", sa.Integer(), nullable=False),
        sa.Column("score_percent", sa.Float(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("ease_factor", sa.Float(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # La línea y el bando son lo que identifica un drill: es lo que hace
        # idempotente la generación, que se pide a mano y se repite.
        sa.UniqueConstraint("player_color", "line_uci", name="uq_drill_color_line"),
    )
    # La cola de repaso se pide siempre igual —"lo que vence hasta ahora, lo
    # más atrasado primero"—, igual que la de los puzzles.
    op.create_index("ix_opening_drills_due_at", "opening_drills", ["due_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_opening_drills_due_at", table_name="opening_drills")
    op.drop_table("opening_drills")

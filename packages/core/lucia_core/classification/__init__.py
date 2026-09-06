"""Clasifica una jugada ya jugada: Mejor / Excelente / Buena / Imprecisión /
Error / Blunder / Perdió el mate (RF-2.2).

Los umbrales están en centésimas de probabilidad de victoria (win%), no en
centipawns crudos, tal como pide RF-2.3, y son un `dataclass` para poder
ajustarlos sin tocar la lógica. La categoría "book" (jugada de teoría) queda
fuera hasta integrar la base de aperturas ECO (ver `lucia_core.openings`,
pendiente); nunca se produce todavía.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

import chess
import chess.engine

from lucia_core.accuracy import win_percent

MoveClassification = Literal[
    "best", "excellent", "good", "book", "inaccuracy", "mistake", "blunder", "missed_win"
]


class EvaluatedPosition(Protocol):
    """Lo que `classify_move` necesita de una posición evaluada. No importa
    `PositionEval` de `lucia_core.analysis` a propósito —`analysis` importa
    de aquí para construir `AnalyzedGame`, y un import en sentido contrario
    crearía un ciclo—; cualquier objeto con esta forma sirve (duck typing)."""

    ply: int
    turn: chess.Color
    score: chess.engine.PovScore
    best_move: chess.Move | None


@dataclass(frozen=True)
class ClassificationThresholds:
    """Pérdida máxima de win% (0-100) para cada categoría; lo que sobra cae
    en la siguiente. Documentados y ajustables (RF-2.2)."""

    excellent_max_loss: float = 2.0
    good_max_loss: float = 5.0
    inaccuracy_max_loss: float = 10.0
    mistake_max_loss: float = 20.0
    # loss >= mistake_max_loss => blunder


DEFAULT_THRESHOLDS = ClassificationThresholds()


def classify_move(
    before: EvaluatedPosition,
    after: EvaluatedPosition,
    played: chess.Move,
    thresholds: ClassificationThresholds | None = None,
) -> tuple[MoveClassification, float, float]:
    """Clasifica la jugada `played`, que llevó de `before` a `after`.

    Devuelve `(clasificación, win% antes, win% después)`, ambos porcentajes
    desde el punto de vista de quien jugó (`before.turn`).
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    mover = before.turn
    win_before = win_percent(before.score.pov(mover), ply=before.ply)
    win_after = win_percent(after.score.pov(mover), ply=after.ply)

    if _perdio_mate_forzado(before, after, mover):
        return "missed_win", win_before, win_after

    if before.best_move is not None and played == before.best_move:
        return "best", win_before, win_after

    perdida = max(0.0, win_before - win_after)
    if perdida < thresholds.excellent_max_loss:
        return "excellent", win_before, win_after
    if perdida < thresholds.good_max_loss:
        return "good", win_before, win_after
    if perdida < thresholds.inaccuracy_max_loss:
        return "inaccuracy", win_before, win_after
    if perdida < thresholds.mistake_max_loss:
        return "mistake", win_before, win_after
    return "blunder", win_before, win_after


def _perdio_mate_forzado(
    before: EvaluatedPosition, after: EvaluatedPosition, mover: chess.Color
) -> bool:
    """Tenía mate forzado a favor y la jugada lo dejó escapar, aunque la
    posición siga siendo ganadora en centipawns: los umbrales de win% no
    distinguen bien entre "mate en 3" y "ganando por una torre" porque ambos
    saturan cerca del 100%, así que se comprueba aparte."""
    antes = before.score.pov(mover)
    despues = after.score.pov(mover)
    tenia_mate = antes.is_mate() and (antes.mate() or 0) > 0
    sigue_con_mate = despues.is_mate() and (despues.mate() or 0) > 0
    return tenia_mate and not sigue_con_mate

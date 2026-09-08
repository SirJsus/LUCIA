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
    mover_color = before.turn
    win_before = win_percent(before.score.pov(mover_color), ply=before.ply)
    win_after = win_percent(after.score.pov(mover_color), ply=after.ply)

    if _missed_forced_mate(before, after, mover_color):
        return "missed_win", win_before, win_after

    if before.best_move is not None and played == before.best_move:
        return "best", win_before, win_after

    win_percent_loss = max(0.0, win_before - win_after)
    if win_percent_loss < thresholds.excellent_max_loss:
        return "excellent", win_before, win_after
    if win_percent_loss < thresholds.good_max_loss:
        return "good", win_before, win_after
    if win_percent_loss < thresholds.inaccuracy_max_loss:
        return "inaccuracy", win_before, win_after
    if win_percent_loss < thresholds.mistake_max_loss:
        return "mistake", win_before, win_after
    return "blunder", win_before, win_after


def _missed_forced_mate(
    before: EvaluatedPosition, after: EvaluatedPosition, mover_color: chess.Color
) -> bool:
    """Tenía mate forzado a favor y la jugada lo dejó escapar, aunque la
    posición siga siendo ganadora en centipawns: los umbrales de win% no
    distinguen bien entre "mate en 3" y "ganando por una torre" porque ambos
    saturan cerca del 100%, así que se comprueba aparte."""
    had_forced_mate = _has_forced_mate(before.score.pov(mover_color))
    still_has_forced_mate = _has_forced_mate(after.score.pov(mover_color))
    return had_forced_mate and not still_has_forced_mate


def _has_forced_mate(score: chess.engine.Score) -> bool:
    """Si la puntuación es un mate **a favor** de quien la mira.

    No sirve mirar `mate() > 0`: el mate ya dado vale `#+0` (`MateGiven`), con
    `mate() == 0`, igual que el mate recibido (`#-0`), así que por ahí la
    jugada que remata la partida contaba como mate perdido. Esa puntuación
    terminal no la da el motor: la pone `_terminal_score` de
    `lucia_core.analysis` al llegar a una posición sin jugadas legales. El
    orden de `Score` sí los distingue: todo mate a favor está por encima de
    cualquier evaluación en centipeones, y todo mate en contra, por debajo."""
    return score.is_mate() and score > chess.engine.Cp(0)

from dataclasses import dataclass

import chess
import chess.engine
from lucia_core.classification import ClassificationThresholds, classify_move


@dataclass
class FakeEvaluatedPosition:
    """Satisface el `Protocol EvaluatedPosition` sin depender de
    `lucia_core.analysis` (ver docstring de `EvaluatedPosition`)."""

    ply: int
    turn: chess.Color
    score: chess.engine.PovScore
    best_move: chess.Move | None


E4 = chess.Move.from_uci("e2e4")
D4 = chess.Move.from_uci("d2d4")


def _pos(
    ply: int, cp: int, best_move: chess.Move | None, mate: int | None = None
) -> FakeEvaluatedPosition:
    score = chess.engine.Mate(mate) if mate is not None else chess.engine.Cp(cp)
    return FakeEvaluatedPosition(
        ply=ply,
        turn=chess.WHITE,
        score=chess.engine.PovScore(score, chess.WHITE),
        best_move=best_move,
    )


def test_playing_the_engine_best_move_is_best() -> None:
    before = _pos(0, cp=20, best_move=E4)
    after = _pos(1, cp=25, best_move=D4)
    classification, _, _ = classify_move(before, after, played=E4)
    assert classification == "best"


def test_small_win_percent_loss_is_excellent() -> None:
    before = _pos(10, cp=50, best_move=D4)
    after = _pos(11, cp=48, best_move=D4)  # casi la misma eval: perdida de win% mínima
    classification, _, _ = classify_move(before, after, played=E4)
    assert classification == "excellent"


def test_big_win_percent_loss_is_blunder() -> None:
    before = _pos(10, cp=200, best_move=D4)  # muy buena posición
    after = _pos(11, cp=-400, best_move=D4)  # se hunde tras la jugada
    classification, win_before, win_after = classify_move(before, after, played=E4)
    assert classification == "blunder"
    assert win_before > win_after


def test_thresholds_are_adjustable() -> None:
    before = _pos(10, cp=100, best_move=D4)
    after = _pos(11, cp=50, best_move=D4)
    strict_thresholds = ClassificationThresholds(excellent_max_loss=0.1)
    classification, _, _ = classify_move(before, after, played=E4, thresholds=strict_thresholds)
    assert classification != "excellent"  # con el umbral por defecto sí lo sería


def test_losing_a_forced_mate_is_missed_win_even_when_still_winning() -> None:
    before = _pos(10, cp=0, best_move=D4, mate=3)  # mate en 3 a favor
    after = _pos(11, cp=500, best_move=D4)  # deja de haber mate, aunque sigue ganando mucho
    classification, _, _ = classify_move(before, after, played=E4)
    assert classification == "missed_win"


def test_keeping_the_forced_mate_is_not_missed_win() -> None:
    before = _pos(10, cp=0, best_move=E4, mate=3)
    after = _pos(11, cp=0, best_move=D4, mate=2)  # sigue habiendo mate, más cerca incluso
    classification, _, _ = classify_move(before, after, played=E4)
    assert classification == "best"  # jugó la mejor jugada del motor

from dataclasses import dataclass

import chess
import chess.engine
from lucia_core.classification import ClassificationThresholds, classify_move


@dataclass
class PosicionFalsa:
    """Satisface el `Protocol EvaluatedPosition` sin depender de
    `lucia_core.analysis` (ver docstring de `EvaluatedPosition`)."""

    ply: int
    turn: chess.Color
    score: chess.engine.PovScore
    best_move: chess.Move | None


E4 = chess.Move.from_uci("e2e4")
D4 = chess.Move.from_uci("d2d4")


def _pos(ply: int, cp: int, mejor: chess.Move | None, mate: int | None = None) -> PosicionFalsa:
    puntaje = chess.engine.Mate(mate) if mate is not None else chess.engine.Cp(cp)
    return PosicionFalsa(
        ply=ply,
        turn=chess.WHITE,
        score=chess.engine.PovScore(puntaje, chess.WHITE),
        best_move=mejor,
    )


def test_jugar_la_mejor_jugada_del_motor_es_best() -> None:
    antes = _pos(0, cp=20, mejor=E4)
    despues = _pos(1, cp=25, mejor=D4)
    clasificacion, _, _ = classify_move(antes, despues, played=E4)
    assert clasificacion == "best"


def test_pequena_perdida_es_excelente() -> None:
    antes = _pos(10, cp=50, mejor=D4)
    despues = _pos(11, cp=48, mejor=D4)  # casi la misma eval: perdida de win% mínima
    clasificacion, _, _ = classify_move(antes, despues, played=E4)
    assert clasificacion == "excellent"


def test_perdida_grande_es_blunder() -> None:
    antes = _pos(10, cp=200, mejor=D4)  # muy buena posición
    despues = _pos(11, cp=-400, mejor=D4)  # se hunde tras la jugada
    clasificacion, win_antes, win_despues = classify_move(antes, despues, played=E4)
    assert clasificacion == "blunder"
    assert win_antes > win_despues


def test_umbrales_son_ajustables() -> None:
    antes = _pos(10, cp=100, mejor=D4)
    despues = _pos(11, cp=50, mejor=D4)
    umbrales_estrictos = ClassificationThresholds(excellent_max_loss=0.1)
    clasificacion, _, _ = classify_move(antes, despues, played=E4, thresholds=umbrales_estrictos)
    assert clasificacion != "excellent"  # con el umbral por defecto sí lo sería


def test_perder_mate_forzado_es_missed_win_aunque_siga_ganando() -> None:
    antes = _pos(10, cp=0, mejor=D4, mate=3)  # mate en 3 a favor
    despues = _pos(11, cp=500, mejor=D4)  # deja de haber mate, aunque sigue ganando mucho
    clasificacion, _, _ = classify_move(antes, despues, played=E4)
    assert clasificacion == "missed_win"


def test_mantener_el_mate_forzado_no_es_missed_win() -> None:
    antes = _pos(10, cp=0, mejor=E4, mate=3)
    despues = _pos(11, cp=0, mejor=D4, mate=2)  # sigue habiendo mate, más cerca incluso
    clasificacion, _, _ = classify_move(antes, despues, played=E4)
    assert clasificacion == "best"  # jugó la mejor jugada del motor

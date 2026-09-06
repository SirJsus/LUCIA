"""Evalúa una partida completa, posición por posición (RF-2.1).

Una partida de N jugadas produce N+1 evaluaciones (la inicial y una tras cada
jugada), no 2·N: evaluar cada posición una sola vez —en vez de "antes" y
"después" de cada jugada por separado— es lo que hacen Lichess y chess.com, y
evita duplicar trabajo del motor, porque la posición "después de la jugada i"
es la misma que "antes de la jugada i+1".
"""

from __future__ import annotations

from dataclasses import dataclass

import chess
import chess.engine

from lucia_core.accuracy import game_accuracy, move_accuracy
from lucia_core.classification import (
    ClassificationThresholds,
    MoveClassification,
    classify_move,
)
from lucia_core.engine import EngineBridge


@dataclass(frozen=True)
class PositionEval:
    """Lo que el motor opina de una posición concreta de la partida."""

    ply: int
    fen: str
    turn: chess.Color
    """De quién es el turno en esta posición (quién va a mover a continuación)."""
    score: chess.engine.PovScore
    best_move: chess.Move | None
    pv: tuple[chess.Move, ...]


@dataclass(frozen=True)
class AnalyzedMove:
    """Una jugada ya jugada, evaluada y clasificada (RF-2.2 / RF-2.3)."""

    ply: int
    color: chess.Color
    san: str
    uci: str
    fen_before: str
    classification: MoveClassification
    accuracy: float
    """Precisión de esta jugada (0-100), fórmula de `lucia_core.accuracy`."""
    win_percent_before: float
    win_percent_after: float
    best_move_uci: str | None


@dataclass(frozen=True)
class AnalyzedGame:
    moves: list[AnalyzedMove]
    white_accuracy: float
    black_accuracy: float


async def evaluate_positions(
    engine: EngineBridge, board: chess.Board, moves: list[chess.Move]
) -> list[PositionEval]:
    """Evalúa la posición inicial y la que sigue a cada jugada de `moves`."""
    posiciones: list[PositionEval] = []
    actual = board.copy()
    for ply in range(len(moves) + 1):
        lineas = await engine.analyse(actual)
        mejor = lineas[0]
        pv = mejor.get("pv") or []
        posiciones.append(
            PositionEval(
                ply=ply,
                fen=actual.fen(),
                turn=actual.turn,
                score=mejor["score"],
                best_move=pv[0] if pv else None,
                pv=tuple(pv),
            )
        )
        if ply < len(moves):
            actual.push(moves[ply])
    return posiciones


async def analyze_game(
    engine: EngineBridge,
    board: chess.Board,
    moves: list[chess.Move],
    thresholds: ClassificationThresholds | None = None,
) -> AnalyzedGame:
    """Evalúa, clasifica y calcula la precisión de una partida completa."""
    posiciones = await evaluate_positions(engine, board, moves)

    analizadas: list[AnalyzedMove] = []
    actual = board.copy()
    for i, move in enumerate(moves):
        antes, despues = posiciones[i], posiciones[i + 1]
        clasificacion, win_antes, win_despues = classify_move(antes, despues, move, thresholds)
        analizadas.append(
            AnalyzedMove(
                ply=i,
                color=antes.turn,
                san=actual.san(move),
                uci=move.uci(),
                fen_before=antes.fen,
                classification=clasificacion,
                accuracy=move_accuracy(win_antes, win_despues),
                win_percent_before=win_antes,
                win_percent_after=win_despues,
                best_move_uci=antes.best_move.uci() if antes.best_move else None,
            )
        )
        actual.push(move)

    blancas = game_accuracy([m.accuracy for m in analizadas if m.color == chess.WHITE])
    negras = game_accuracy([m.accuracy for m in analizadas if m.color == chess.BLACK])
    return AnalyzedGame(moves=analizadas, white_accuracy=blancas, black_accuracy=negras)

"""Evalúa una partida completa, posición por posición (RF-2.1).

Una partida de N jugadas produce N+1 evaluaciones (la inicial y una tras cada
jugada), no 2·N: evaluar cada posición una sola vez —en vez de "antes" y
"después" de cada jugada por separado— es lo que hacen Lichess y chess.com, y
evita duplicar trabajo del motor, porque la posición "después de la jugada i"
es la misma que "antes de la jugada i+1".
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

import chess
import chess.engine

from lucia_core.accuracy import game_accuracy, move_accuracy
from lucia_core.classification import (
    ClassificationThresholds,
    MoveClassification,
    classify_move,
)
from lucia_core.phases import Phase, phases_by_ply

OnPosition = Callable[[int, int], Awaitable[None]]
"""Callback de progreso: `on_position(ply_evaluado, total_de_jugadas)`."""


class AnalysingEngine(Protocol):
    """Lo que `evaluate_positions` necesita de un motor: analizar una
    posición. No exige `EngineBridge` en concreto (`Protocol` estructural)
    para que `apps/api` pueda envolverlo con caché por FEN (RF-2.7) sin que
    `lucia_core` sepa nada de bases de datos."""

    async def analyse(self, board: chess.Board) -> list[chess.engine.InfoDict]: ...


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
    phase: Phase
    """Fase de la partida al jugarse (RF-3.3), de `lucia_core.phases`."""
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
    engine: AnalysingEngine,
    board: chess.Board,
    moves: list[chess.Move],
    on_position: OnPosition | None = None,
) -> list[PositionEval]:
    """Evalúa la posición inicial y la que sigue a cada jugada de `moves`.

    Si se pasa `on_position`, se llama tras cada evaluación con
    `(ply_evaluado, total_de_jugadas)` — pensado para reportar progreso
    (RF-2.4) en un análisis largo, sin que este módulo sepa nada de colas ni
    de WebSockets.
    """
    posiciones: list[PositionEval] = []
    actual = board.copy()
    for ply in range(len(moves) + 1):
        if actual.is_game_over():
            # Posición terminal: el resultado ya está decidido y no hay jugada
            # que buscar. Además hay que evitar preguntarle al motor: Lc0 se
            # queda colgado indefinidamente si se le pide `go` en una posición
            # sin jugadas legales, lo que dejaba tieso el análisis de
            # cualquier partida terminada en jaque mate.
            posiciones.append(
                PositionEval(
                    ply=ply,
                    fen=actual.fen(),
                    turn=actual.turn,
                    score=_score_terminal(actual),
                    best_move=None,
                    pv=(),
                )
            )
        else:
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
        if on_position is not None:
            await on_position(ply, len(moves))
        if ply < len(moves):
            actual.push(moves[ply])
    return posiciones


def _score_terminal(board: chess.Board) -> chess.engine.PovScore:
    """Evaluación de una posición ya terminada, sin consultar al motor.

    `Mate(0)` es la forma que tiene `python-chess` de decir "a quien le toca
    mover ya está mateado". El resto de finales (ahogado, material
    insuficiente, repetición, 50 jugadas) son tablas.
    """
    puntaje = chess.engine.Mate(0) if board.is_checkmate() else chess.engine.Cp(0)
    return chess.engine.PovScore(puntaje, board.turn)


async def analyze_game(
    engine: AnalysingEngine,
    board: chess.Board,
    moves: list[chess.Move],
    thresholds: ClassificationThresholds | None = None,
    on_position: OnPosition | None = None,
) -> AnalyzedGame:
    """Evalúa, clasifica y calcula la precisión de una partida completa."""
    posiciones = await evaluate_positions(engine, board, moves, on_position)

    # Las fases se calculan sobre los tableros, no sobre las evaluaciones: no
    # hace falta el motor para saber si una posición es un final.
    tableros: list[chess.Board] = []
    recorrido = board.copy()
    for move in moves:
        tableros.append(recorrido.copy())
        recorrido.push(move)
    fases = phases_by_ply(tableros)

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
                phase=fases[i],
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

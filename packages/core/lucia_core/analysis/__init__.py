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


class AnalyzingEngine(Protocol):
    """Lo que `evaluate_positions` necesita de un motor: analizar una
    posición. No exige `EngineBridge` en concreto (`Protocol` estructural)
    para que `apps/api` pueda envolverlo con caché por FEN (RF-2.7) sin que
    `lucia_core` sepa nada de bases de datos."""

    async def analyze(self, board: chess.Board) -> list[chess.engine.InfoDict]: ...


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
    engine: AnalyzingEngine,
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
    position_evals: list[PositionEval] = []
    current_board = board.copy()
    for ply in range(len(moves) + 1):
        if current_board.is_game_over():
            # Posición terminal: el resultado ya está decidido y no hay jugada
            # que buscar. Además hay que evitar preguntarle al motor: Lc0 se
            # queda colgado indefinidamente si se le pide `go` en una posición
            # sin jugadas legales, lo que dejaba tieso el análisis de
            # cualquier partida terminada en jaque mate.
            position_evals.append(
                PositionEval(
                    ply=ply,
                    fen=current_board.fen(),
                    turn=current_board.turn,
                    score=_terminal_score(current_board),
                    best_move=None,
                    pv=(),
                )
            )
        else:
            engine_lines = await engine.analyze(current_board)
            best_line = engine_lines[0]
            pv = best_line.get("pv") or []
            position_evals.append(
                PositionEval(
                    ply=ply,
                    fen=current_board.fen(),
                    turn=current_board.turn,
                    score=best_line["score"],
                    best_move=pv[0] if pv else None,
                    pv=tuple(pv),
                )
            )
        if on_position is not None:
            await on_position(ply, len(moves))
        if ply < len(moves):
            current_board.push(moves[ply])
    return position_evals


def _terminal_score(board: chess.Board) -> chess.engine.PovScore:
    """Evaluación de una posición ya terminada, sin consultar al motor.

    `Mate(0)` es la forma que tiene `python-chess` de decir "a quien le toca
    mover ya está mateado". El resto de finales (ahogado, material
    insuficiente, repetición, 50 jugadas) son tablas.
    """
    score = chess.engine.Mate(0) if board.is_checkmate() else chess.engine.Cp(0)
    return chess.engine.PovScore(score, board.turn)


async def analyze_game(
    engine: AnalyzingEngine,
    board: chess.Board,
    moves: list[chess.Move],
    thresholds: ClassificationThresholds | None = None,
    on_position: OnPosition | None = None,
) -> AnalyzedGame:
    """Evalúa, clasifica y calcula la precisión de una partida completa.

    `board` es la posición de partida y `moves` la línea principal jugada
    desde ella: quien llama debe pasar la posición real de la partida (en
    `apps/api`, `pgn_game.board()`), no un `chess.Board()` recién creado, o
    las jugadas de una partida con `[SetUp "1"]` + `[FEN ...]` se replicarán
    sobre un tablero que no es el suyo.
    """
    position_evals = await evaluate_positions(engine, board, moves, on_position)

    # Las fases se calculan sobre los tableros, no sobre las evaluaciones: no
    # hace falta el motor para saber si una posición es un final.
    boards_by_ply: list[chess.Board] = []
    replay_board = board.copy()
    for move in moves:
        boards_by_ply.append(replay_board.copy())
        replay_board.push(move)
    phases = phases_by_ply(boards_by_ply)

    analyzed_moves: list[AnalyzedMove] = []
    current_board = board.copy()
    for i, move in enumerate(moves):
        before, after = position_evals[i], position_evals[i + 1]
        classification, win_before, win_after = classify_move(before, after, move, thresholds)
        analyzed_moves.append(
            AnalyzedMove(
                ply=i,
                color=before.turn,
                san=current_board.san(move),
                uci=move.uci(),
                fen_before=before.fen,
                classification=classification,
                phase=phases[i],
                accuracy=move_accuracy(win_before, win_after),
                win_percent_before=win_before,
                win_percent_after=win_after,
                best_move_uci=before.best_move.uci() if before.best_move else None,
            )
        )
        current_board.push(move)

    white_accuracy = game_accuracy([m.accuracy for m in analyzed_moves if m.color == chess.WHITE])
    black_accuracy = game_accuracy([m.accuracy for m in analyzed_moves if m.color == chess.BLACK])
    return AnalyzedGame(
        moves=analyzed_moves, white_accuracy=white_accuracy, black_accuracy=black_accuracy
    )

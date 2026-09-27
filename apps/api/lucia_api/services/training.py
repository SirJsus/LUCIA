"""Entrenamiento desde los errores propios (RF-4.1): generar puzzles y
comprobar cada intento.

La cola de repaso y el apunte de cómo fue no están aquí sino en
`services/review.py`, que es el mismo para los puzzles y para los drills de
apertura: lo propio de un puzzle es de dónde sale y qué respuestas se le
aceptan, no cuándo vuelve.

Este módulo es el puente entre la base y `lucia_core.training`, igual que
`services/insights.py` lo es con `lucia_core.insights`: aquí se carga el
material —los errores que el análisis ya detectó y las alternativas que el
motor ya guardó (RF-10.1)— y allí viven las dos reglas, que son puras y se
prueban solas: cuándo vuelve un puzzle (SM-2) y qué respuestas se le aceptan
(RF-10.3).

**De dónde salen los puzzles.** De `analyzed_moves`, del análisis terminado
más reciente de cada partida (`latest_analysis_ids`, el mismo criterio que las
estadísticas), y solo de las jugadas **del usuario**: un error del rival dice
cómo juega el otro. Al contrario que los patrones, que se deducen al leer y no
se guardan (ADR-0008), un puzzle **sí se persiste**, porque lleva encima algo
que no está en ninguna otra parte: el historial de repasos.

Lo consume `routers/training.py`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import chess
from lucia_core.classification import MoveClassification
from lucia_core.training import NEW_REVIEW_STATE, equivalent_solutions, grade_of
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove, Game, Puzzle
from lucia_api.services.analysis import alternatives_of, cached_alternatives_by_analysis
from lucia_api.services.insights import latest_analysis_ids, mover_win_percent
from lucia_api.services.review import record_review

PUZZLE_CLASSIFICATIONS: tuple[MoveClassification, ...] = ("mistake", "blunder", "missed_win")
"""Qué errores dan puzzle. Las imprecisiones quedan fuera a propósito: una
jugada que pierde menos de diez puntos de probabilidad de victoria no tiene
una respuesta que encontrar, tiene un matiz que discutir, y como puzzle solo
enseñaría a adivinar la preferencia del motor.

No hace falta descartar además los errores en posiciones ya perdidas: la
probabilidad de victoria se encarga sola, porque desde un 4 % no se pueden
perder los veinte puntos que definen un blunder.
"""


async def generate_puzzles(session: AsyncSession, username: str) -> int:
    """Crea los puzzles que falten a partir de los errores ya analizados del
    jugador, y devuelve cuántos se crearon.

    Es idempotente: la clave `(partida, jugada)` es única, así que volver a
    pulsar tras analizar más partidas añade solo lo nuevo y **no toca el
    estado de repaso de lo que ya había**.
    """
    rows = (
        await session.execute(
            select(AnalyzedMove, Analysis, Game)
            .join(Analysis, AnalyzedMove.analysis_id == Analysis.id)
            .join(Game, Analysis.game_id == Game.id)
            .where(
                Analysis.id.in_(latest_analysis_ids()),
                AnalyzedMove.classification.in_(PUZZLE_CLASSIFICATIONS),
            )
            .order_by(Game.id, AnalyzedMove.ply)
        )
    ).all()
    own_mistakes = [
        (move, analysis, game)
        for move, analysis, game in rows
        if move.color == _player_color(game, username)
    ]
    if not own_mistakes:
        return 0

    # Las alternativas de un análisis anterior a RF-10.1 no están en su fila;
    # se rescatan de la caché de posiciones, igual que hacen el visor y los
    # patrones (ADR-0007). Sin ellas el puzzle se queda con la única jugada
    # que el análisis guardó, que es lo máximo que se puede afirmar.
    cached_by_analysis = await cached_alternatives_by_analysis(
        session, ((move, analysis) for move, analysis, _game in own_mistakes)
    )

    already_generated = set((await session.execute(select(Puzzle.game_id, Puzzle.ply))).all())
    created = 0
    for move, analysis, game in own_mistakes:
        if (game.id, move.ply) in already_generated:
            continue
        solutions = _solutions_of(move, alternatives_of(move, cached_by_analysis[analysis.id]))
        if not solutions:
            continue  # sin ninguna jugada que dar por buena no hay puzzle que plantear
        session.add(
            Puzzle(
                game_id=game.id,
                ply=move.ply,
                fen=move.fen_before,
                played_uci=move.uci,
                solutions_json=list(solutions),
                classification=move.classification,
                win_percent_before=move.win_percent_before,
                win_percent_after=move.win_percent_after,
                repetitions=NEW_REVIEW_STATE.repetitions,
                interval_days=NEW_REVIEW_STATE.interval_days,
                ease_factor=NEW_REVIEW_STATE.ease_factor,
            )
        )
        already_generated.add((game.id, move.ply))
        created += 1

    await session.commit()
    return created


def _player_color(game: Game, username: str) -> str:
    return "white" if game.white_username.lower() == username.lower() else "black"


def _solutions_of(move: AnalyzedMove, alternatives: list[dict]) -> tuple[str, ...]:
    """Las jugadas que se aceptan como respuesta a este puzzle (RF-10.3).

    Sale de las líneas que el motor veía en la posición, comparadas entre sí
    en probabilidad de victoria desde el punto de vista de quien resuelve. Si
    el análisis es anterior a RF-10.1 y sus posiciones ya no están en la
    caché, queda `best_move_uci`: una sola respuesta buena, que es peor
    puzzle pero no uno falso.
    """
    candidates = [
        (line["pv"][0], mover_win_percent(line, move.color, move.ply))
        for line in alternatives
        if line["pv"]
    ]
    if candidates:
        return equivalent_solutions(candidates)
    return (move.best_move_uci,) if move.best_move_uci else ()


async def count_puzzles(session: AsyncSession) -> int:
    """Cuántos puzzles hay en total, tocando o no."""
    return (await session.execute(select(func.count(Puzzle.id)))).scalar_one()


@dataclass(frozen=True)
class PuzzleAnswer:
    """Cómo fue el intento, y todo lo que la pantalla puede enseñar ya."""

    correct: bool
    reviewed: bool
    """Si el puzzle se dio por terminado y su repaso quedó anotado. Un fallo
    con intentos por delante no lo está: la pantalla deja volver a probar sin
    que el error cuente dos veces."""
    solutions_san: list[str]
    """Las respuestas buenas, en notación algebraica. Vacío mientras el puzzle
    siga abierto: enseñarlas sería resolverlo."""
    played_san: str | None
    """Lo que se jugó en la partida, que casi nunca es la solución. Solo al
    cerrar, por lo mismo."""


async def answer_puzzle(
    session: AsyncSession,
    puzzle: Puzzle,
    answer_uci: str | None,
    attempt_number: int,
    now: dt.datetime,
) -> PuzzleAnswer:
    """Comprueba una respuesta y, si el puzzle queda cerrado, anota el repaso.

    `answer_uci` a `None` es rendirse: cierra el puzzle como fallado y enseña
    la solución. Una respuesta equivocada con el puzzle aún abierto no anota
    nada — el usuario puede volver a intentarlo, y es `attempt_number` (cuántas veces
    lo ha intentado, contando esta) lo que distingue después acertar a la
    primera de acertar tropezando.
    """
    correct = answer_uci is not None and answer_uci in puzzle.solutions_json
    reviewed = correct or answer_uci is None
    if not reviewed:
        return PuzzleAnswer(correct=False, reviewed=False, solutions_san=[], played_san=None)

    # `attempt_number` cuenta el intento en curso (el primero es 1) y `grade_of`
    # cuenta los fallos previos, que es la convención común a los dos
    # ejercicios.
    record_review(puzzle, grade_of(correct, attempt_number - 1), now)
    await session.commit()
    board = chess.Board(puzzle.fen)
    return PuzzleAnswer(
        correct=correct,
        reviewed=True,
        solutions_san=[_san_of(board, uci) for uci in puzzle.solutions_json],
        played_san=_san_of(board, puzzle.played_uci),
    )


def _san_of(board: chess.Board, uci: str) -> str:
    """La jugada en notación algebraica, que es como se lee en pantalla. Si ya
    no encaja en la posición se devuelve tal cual: decir "e2e4" es peor que
    decir "e4", pero mejor que no decir nada."""
    try:
        return board.san(chess.Move.from_uci(uci))
    except (ValueError, AssertionError):
        return uci


def solver_color(puzzle: Puzzle) -> str:
    """De qué color juega quien resuelve: el turno de la posición. La pantalla
    lo necesita para orientar el tablero desde su lado, como el visor."""
    return "white" if chess.Board(puzzle.fen).turn == chess.WHITE else "black"


def opponent_username(puzzle: Puzzle, game: Game) -> str:
    """Contra quién se cometió el error: el bando contrario a quien resuelve."""
    return game.black_username if solver_color(puzzle) == "white" else game.white_username

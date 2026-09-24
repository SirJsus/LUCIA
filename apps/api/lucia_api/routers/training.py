"""POST /training/puzzles, GET /training/puzzles y POST
/training/puzzles/{id}/answer — entrenamiento desde los errores propios con
repetición espaciada (RF-4.1, con RF-10.3).

Los tres endpoints siguen el ciclo de la pantalla: generar los puzzles a
partir de lo ya analizado, pedir los que tocan hoy, y contestarlos.

**Qué se manda y qué no.** La posición sale con lo justo para plantear el
problema: ni la jugada que se hizo en la partida ni la solución viajan hasta
que el puzzle se cierra, porque cualquiera de las dos lo resuelve. Eso obliga
a comprobar la respuesta en el servidor, que es donde está el dato — y de
paso es lo que permite aceptar cualquier jugada equivalente (RF-10.3) sin que
el cliente tenga que saber cuáles son.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Game, Puzzle
from lucia_api.dependencies import resolved_username
from lucia_api.services.review import (
    DEFAULT_QUEUE_LIMIT,
    MAX_QUEUE_LIMIT,
    review_queue,
    utc_now,
)
from lucia_api.services.training import (
    answer_puzzle,
    count_puzzles,
    generate_puzzles,
    opponent_username,
    solver_color,
)

router = APIRouter(prefix="/training", tags=["training"])


class PuzzleOut(BaseModel):
    """Un puzzle por resolver, sin nada que lo resuelva."""

    id: int
    fen: str
    """La posición a resolver. Mueve quien cometió el error."""
    player_color: str
    """"white" | "black": de qué color juega quien resuelve. Se deduce del
    turno del FEN, y va aparte para que la pantalla oriente el tablero desde
    su lado sin tener que leerlo."""
    game_id: int
    ply: int
    """De qué partida y de qué jugada salió, para poder ir a verla en el visor
    una vez resuelto."""
    opponent: str
    played_at: dt.datetime
    due_at: dt.datetime
    repetitions: int
    """Cuántas veces seguidas se ha acertado ya. La pantalla distingue con él
    un puzzle nuevo de uno que vuelve."""


class PuzzleQueueOut(BaseModel):
    puzzles: list[PuzzleOut]
    due: int
    """Cuántos vencen ahora mismo, que pueden ser más de los que caben en la
    tanda."""
    total: int
    next_due_at: dt.datetime | None
    """Cuándo vuelve a tocar, si ahora no toca nada. `null` cuando no hay
    ningún puzzle generado."""


class PuzzleGenerationOut(BaseModel):
    created: int
    total: int


class PuzzleAnswerIn(BaseModel):
    uci: str | None = None
    """La jugada intentada, o `null` para rendirse y ver la solución."""
    attempt_number: int = Field(default=1, ge=1)
    """Cuántas veces se ha intentado este puzzle, contando esta. Lo lleva la
    pantalla porque es suyo el ciclo de reintentos; el servidor solo lo usa
    para distinguir acertar a la primera de acertar tropezando."""


class PuzzleAnswerOut(BaseModel):
    correct: bool
    reviewed: bool
    """Si el puzzle quedó cerrado y su repaso anotado. Con `false` la pantalla
    deja volver a intentarlo."""
    solutions_san: list[str]
    """Las respuestas buenas (RF-10.3), de mejor a peor. Vacío mientras el
    puzzle siga abierto."""
    played_san: str | None
    """Lo que se jugó en la partida. `null` mientras siga abierto."""
    classification: str | None
    """Qué fue aquel error: "blunder", "mistake" o "missed_win"."""
    win_percent_before: float | None
    win_percent_after: float | None
    """Lo que costó el error, en probabilidad de victoria de quien lo cometió.

    Estos tres van a `null` mientras el puzzle siga abierto, por lo mismo que
    la solución: saber que aquello fue un blunder de treinta puntos dice que
    aquí había algo gordo que ver, y eso es media respuesta. Se mandan al
    cerrarlo, que es cuando la pantalla los enseña."""
    due_at: dt.datetime | None
    interval_days: int | None
    """Cuándo vuelve este puzzle y dentro de cuántos días, para poder decirlo
    en pantalla en vez de dejar que reaparezca sin explicación. `null`
    mientras siga abierto: todavía no se ha anotado ningún repaso."""


@router.post("/puzzles", response_model=PuzzleGenerationOut)
async def generate_player_puzzles(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> PuzzleGenerationOut:
    """Crea puzzles a partir de los errores de las partidas ya analizadas.

    Se pide a mano y no al analizar: quien entrena decide cuándo renovar su
    baraja, y así analizar una tanda de partidas no cambia la cola de repaso
    por sorpresa. Volver a pulsar solo añade lo nuevo.
    """
    created = await generate_puzzles(session, resolved_username(username))
    return PuzzleGenerationOut(created=created, total=await count_puzzles(session))


@router.get("/puzzles", response_model=PuzzleQueueOut)
async def player_puzzle_queue(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_QUEUE_LIMIT)] = DEFAULT_QUEUE_LIMIT,
) -> PuzzleQueueOut:
    """Los puzzles que toca repasar ahora, del más atrasado al más reciente."""
    queue = await review_queue(session, Puzzle, utc_now(), limit)
    games = await _games_of(session, queue.items)
    return PuzzleQueueOut(
        puzzles=[_to_puzzle_out(puzzle, games[puzzle.game_id]) for puzzle in queue.items],
        due=queue.due,
        total=queue.total,
        next_due_at=queue.next_due_at,
    )


@router.post("/puzzles/{puzzle_id}/answer", response_model=PuzzleAnswerOut)
async def answer_player_puzzle(
    puzzle_id: int,
    body: PuzzleAnswerIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PuzzleAnswerOut:
    """Comprueba una respuesta y, si cierra el puzzle, anota el repaso."""
    puzzle = await session.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail="ese puzzle no existe")

    answer = await answer_puzzle(session, puzzle, body.uci, body.attempt_number, utc_now())
    if not answer.reviewed:
        # Un puzzle que sigue abierto se va con lo justo: que la respuesta no
        # valía. Todo lo demás que hay en la fila lo resolvería.
        return PuzzleAnswerOut(
            correct=False,
            reviewed=False,
            solutions_san=[],
            played_san=None,
            classification=None,
            win_percent_before=None,
            win_percent_after=None,
            due_at=None,
            interval_days=None,
        )
    return PuzzleAnswerOut(
        correct=answer.correct,
        reviewed=True,
        solutions_san=answer.solutions_san,
        played_san=answer.played_san,
        classification=puzzle.classification,
        win_percent_before=puzzle.win_percent_before,
        win_percent_after=puzzle.win_percent_after,
        due_at=puzzle.due_at,
        interval_days=puzzle.interval_days,
    )


async def _games_of(session: AsyncSession, puzzles: list[Puzzle]) -> dict[int, Game]:
    """Las partidas de una tanda de puzzles, en una sola consulta: de ellas
    salen el rival y la fecha con los que se sitúa cada posición."""
    if not puzzles:
        return {}
    rows = await session.execute(
        select(Game).where(Game.id.in_({puzzle.game_id for puzzle in puzzles}))
    )
    return {game.id: game for game in rows.scalars()}


def _to_puzzle_out(puzzle: Puzzle, game: Game) -> PuzzleOut:
    return PuzzleOut(
        id=puzzle.id,
        fen=puzzle.fen,
        player_color=solver_color(puzzle),
        game_id=puzzle.game_id,
        ply=puzzle.ply,
        opponent=opponent_username(puzzle, game),
        played_at=game.played_at,
        due_at=puzzle.due_at,
        repetitions=puzzle.repetitions,
    )

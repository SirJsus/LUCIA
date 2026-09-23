"""POST /training/drills, GET /training/drills y POST /training/drills/{id}/moves
— drill de aperturas: repetir jugando las líneas donde peor se rinde (RF-4.2).

Los tres endpoints siguen el ciclo de la pantalla, el mismo de los puzzles:
generar los drills a partir de lo que ya se sabe del repertorio y de las
aperturas, pedir los que tocan hoy, y recorrerlos jugada a jugada.

**Qué se manda y qué no.** La línea **no viaja**: es la respuesta. De un drill
abierto se manda la posición que toca jugar y nada más, y el servidor
comprueba cada jugada, contesta por el rival y solo al cerrarlo enseña la
línea entera. Es la misma regla que en `routers/training.py`, y aquí además
es lo que permite que el rival responda sin que el navegador sepa qué viene.

**Por dónde va el drill lo lleva la pantalla** (`ply`), como lleva el número
de intento en los puzzles: el ciclo de reintentos es suyo. El servidor no
guarda progreso, porque un drill a medias no es un estado que valga la pena
conservar — se repite entero o no se repite.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from lucia_core.drills import DrillLine
from lucia_core.training import ReviewGrade
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import OpeningDrill
from lucia_api.dependencies import resolved_username
from lucia_api.services.drills import (
    count_drills,
    drill_line,
    generate_drills,
    get_drill_queue,
    record_review,
)
from lucia_api.services.repertoire import compare_repertoire

router = APIRouter(prefix="/training", tags=["training"])

#: Cuántos drills se reparten de una vez, por lo mismo que los puzzles: una
#: sesión se hace de unos pocos.
DEFAULT_QUEUE_LIMIT = 20
MAX_QUEUE_LIMIT = 100


class DrillOut(BaseModel):
    """Un drill por hacer, sin la línea que lo resuelve."""

    id: int
    reason: str
    """"departure" (aquí te sales de la teoría) u "opening" (esta apertura te
    va mal). Cambia lo que la pantalla cuenta, no cómo se juega."""
    player_color: str
    opening_eco: str | None
    opening_name: str | None
    games: int
    score_percent: float
    """Por qué está en la baraja: cuántas partidas propias lo justifican y qué
    se sacó en ellas (RF-4.2, "las líneas donde mi rendimiento es peor")."""

    fen: str
    """La posición donde hay que hacer la primera jugada. Con negras ya lleva
    hecha la del rival: si no, el tablero estaría esperando a nadie."""
    first_player_ply: int
    """En qué jugada de la línea empieza: 0 con blancas, 1 con negras."""
    preceding_moves_san: list[str]
    """Lo ya jugado para llegar a esa posición, para poder leerlo. Vacío con
    blancas."""
    length_plies: int
    """Cuántas jugadas tiene la línea en total. Es la barra de progreso; no
    dice cuáles son."""

    due_at: dt.datetime
    repetitions: int


class DrillQueueOut(BaseModel):
    drills: list[DrillOut]
    due: int
    total: int
    next_due_at: dt.datetime | None
    positions_missing: int
    """Cuánta teoría le falta al repertorio (RF-3.6). Viaja también aquí y no
    solo en `DrillGenerationOut` porque es una condición de la pantalla y no el
    resultado de haber pulsado un botón: el repertorio se llena a trozos
    (ADR-0010), así que una cola corta puede serlo porque falta teoría y no
    porque se juegue bien, y eso hay que poder saberlo al llegar (fila 99 del
    inventario de docs/07-coherencia-ui.md)."""


class DrillGenerationOut(BaseModel):
    created: int
    total: int
    positions_missing: int
    """Cuánta teoría le falta al repertorio (RF-3.6). Mientras no sea cero hay
    drills que todavía no se pueden generar, y la pantalla manda a refrescar
    en vez de dejar creer que no hay material."""


class DrillMoveIn(BaseModel):
    ply: int = Field(ge=0)
    """En qué jugada de la línea va la pantalla."""
    uci: str | None = None
    """La jugada intentada, o `null` para rendirse y ver la línea entera."""
    wrong_moves: int = Field(default=0, ge=0)
    """Cuántas veces se ha fallado en este drill, sin contar esta. Lo lleva la
    pantalla, como el número de intento de un puzzle, y el servidor solo lo usa
    al cerrar para distinguir recorrer la línea limpia de recorrerla
    tropezando."""


class DrillMoveOut(BaseModel):
    correct: bool
    reply_uci: str | None
    reply_san: str | None
    """Lo que contesta el rival, si la línea sigue. `null` cuando la jugada
    propia cierra la línea, o cuando la intentada era otra."""
    fen: str
    """La posición tras la jugada propia y la respuesta del rival: la de la
    siguiente decisión, o la final."""
    next_ply: int | None
    """Dónde toca acertar la próxima, o `null` si la línea se acabó."""
    finished: bool

    line_san: list[str]
    """La línea entera, en notación algebraica. Vacía mientras el drill siga
    abierto: es la respuesta."""
    due_at: dt.datetime | None
    interval_days: int | None
    """Cuándo vuelve este drill y dentro de cuántos días. `null` mientras siga
    abierto: todavía no se ha anotado ningún repaso."""


@router.post("/drills", response_model=DrillGenerationOut)
async def generate_opening_drills(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> DrillGenerationOut:
    """Crea los drills que falten a partir del repertorio y de las aperturas.

    Se pide a mano, como los puzzles: quien entrena decide cuándo renovar su
    baraja. Volver a pulsar solo añade lo nuevo y no toca el estado de repaso
    de lo que ya había.
    """
    generation = await generate_drills(session, resolved_username(username))
    return DrillGenerationOut(
        created=generation.created,
        total=await count_drills(session),
        positions_missing=generation.positions_missing,
    )


@router.get("/drills", response_model=DrillQueueOut)
async def player_drill_queue(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_QUEUE_LIMIT)] = DEFAULT_QUEUE_LIMIT,
    username: str | None = None,
) -> DrillQueueOut:
    """Los drills que toca repetir ahora, del más atrasado al más reciente, y
    cuánta teoría le falta al repertorio del que salen."""
    queue = await get_drill_queue(session, _now(), limit)
    # La misma comparación que cuenta «Generar líneas», que es de donde sale
    # este número: pedirla entera sale igual de caro —lo que cuesta es cargar
    # las partidas y la teoría, que se hace en las dos— y así hay un solo sitio
    # donde se decide qué posición falta.
    comparison = await compare_repertoire(session, resolved_username(username))
    return DrillQueueOut(
        drills=[_to_drill_out(drill) for drill in queue.drills],
        due=queue.due,
        total=queue.total,
        next_due_at=queue.next_due_at,
        positions_missing=comparison.positions_missing,
    )


@router.post("/drills/{drill_id}/moves", response_model=DrillMoveOut)
async def play_drill_move(
    drill_id: int,
    body: DrillMoveIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DrillMoveOut:
    """Comprueba una jugada de la línea y contesta por el rival.

    Fallar **no** cierra el drill ni enseña la jugada buena: se puede volver a
    intentar, igual que en un puzzle. Rendirse (`uci` a `null`) sí lo cierra,
    como fallado, y entonces se ve la línea entera.
    """
    drill = await session.get(OpeningDrill, drill_id)
    if drill is None:
        raise HTTPException(status_code=404, detail="ese drill no existe")

    line = drill_line(drill)
    if not 0 <= body.ply < len(line.moves_uci) or not line.is_player_ply(body.ply):
        raise HTTPException(
            status_code=422, detail=f"el ply {body.ply} no es una jugada propia de esta línea"
        )

    if body.uci is None:
        return await _close_drill(session, drill, line, correct=False, wrong_moves=body.wrong_moves)
    if body.uci != line.expected_uci_at(body.ply):
        # Sin decir cuál era: se puede volver a intentar, y enseñarla aquí
        # convertiría el reintento en un trámite. La posición no se mueve y se
        # vuelve a pedir la misma jugada.
        return _open_move_out(correct=False, fen=line.board_at(body.ply).fen(), next_ply=body.ply)

    reply_uci = line.reply_uci_after(body.ply)
    if reply_uci is None:
        return await _close_drill(session, drill, line, correct=True, wrong_moves=body.wrong_moves)

    board_before_reply = line.board_at(body.ply + 1)
    return _open_move_out(
        correct=True,
        fen=line.board_at(body.ply + 2).fen(),
        next_ply=body.ply + 2,
        reply_uci=reply_uci,
        reply_san=board_before_reply.san(board_before_reply.parse_uci(reply_uci)),
    )


def _open_move_out(
    *,
    correct: bool,
    fen: str,
    next_ply: int,
    reply_uci: str | None = None,
    reply_san: str | None = None,
) -> DrillMoveOut:
    """La respuesta de un drill que sigue abierto: la posición que hay delante,
    dónde toca acertar y, si la jugada era la buena, lo que contesta el rival.

    Lo que nunca sale de aquí es la línea ni el próximo repaso: lo uno es la
    respuesta y lo otro todavía no ha pasado. En un solo sitio para que no
    pueda escaparse por una de las dos salidas y no por la otra."""
    return DrillMoveOut(
        correct=correct,
        reply_uci=reply_uci,
        reply_san=reply_san,
        fen=fen,
        next_ply=next_ply,
        finished=False,
        line_san=[],
        due_at=None,
        interval_days=None,
    )


async def _close_drill(
    session: AsyncSession,
    drill: OpeningDrill,
    line: DrillLine,
    *,
    correct: bool,
    wrong_moves: int,
) -> DrillMoveOut:
    """Cierra el drill: anota el repaso —y lo guarda— y enseña la línea
    entera, que es lo único que sale de aquí una vez cerrado."""
    record_review(drill, _grade_of(correct, wrong_moves), _now())
    await session.commit()
    return DrillMoveOut(
        correct=correct,
        reply_uci=None,
        reply_san=None,
        fen=line.board_at(len(line.moves_uci)).fen(),
        next_ply=None,
        finished=True,
        line_san=line.moves_san(),
        due_at=drill.due_at,
        interval_days=drill.interval_days,
    )


def _grade_of(correct: bool, wrong_moves: int) -> ReviewGrade:
    """Cómo fue la pasada, en el vocabulario de SM-2: rendirse es fallar,
    recorrer la línea limpia es acertar, y tropezar por el camino queda en
    medio. Es el mismo criterio que con los puzzles, contando fallos de la
    línea entera en vez de intentos de una jugada."""
    if not correct:
        return "failed"
    return "solved" if wrong_moves == 0 else "hesitant"


def _to_drill_out(drill: OpeningDrill) -> DrillOut:
    line = drill_line(drill)
    first_player_ply = line.first_player_ply
    board = line.board_at(first_player_ply)
    return DrillOut(
        id=drill.id,
        reason=drill.reason,
        player_color=drill.player_color,
        opening_eco=drill.opening_eco,
        opening_name=drill.opening_name,
        games=drill.games,
        score_percent=drill.score_percent,
        fen=board.fen(),
        first_player_ply=first_player_ply,
        preceding_moves_san=line.moves_san()[:first_player_ply],
        length_plies=len(line.moves_uci),
        due_at=drill.due_at,
        repetitions=drill.repetitions,
    )


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)

"""GET /games — listar y consultar partidas importadas (RF-5.3)."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Game
from lucia_api.services.games import is_black, is_player, is_white, outcome_of

router = APIRouter(tags=["games"])


class GameSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    white_username: str
    white_rating: int
    white_result: str
    """Resultado tal como lo reporta chess.com: "win" | "checkmated" | "resigned"..."""
    black_username: str
    black_rating: int
    black_result: str
    time_control: str
    time_class: str
    rated: bool
    eco: str | None
    played_at: dt.datetime
    starts_from_custom_position: bool
    """La partida no empieza en la posición estándar (odds chess, Chess960,
    partidas desde posición). Sale del PGN, no de una columna: ver
    `Game.starts_from_custom_position`."""
    platform: str
    """De dónde salió la partida: `"chesscom"` si la trajo el sincronizador
    (RF-1.2), `"manual"` si vino de un archivo PGN (RF-1.5) y `"board"` si es
    un tablero de análisis publicado como partida propia (RF-6.5, ADR-0014).

    El front lo necesita para explicar los huecos: una partida importada a mano
    no trae ratings, ritmo ni control de tiempo, y sin decir de dónde viene,
    cuatro columnas vacías al lado de sus vecinas llenas se leen como un fallo
    de la aplicación (fila 67 del inventario de docs/07-coherencia-ui.md)."""


class GameDetail(GameSummary):
    pgn: str
    clocks_json: list | None


def _filter_conditions(
    *,
    username: str | None,
    color: Literal["white", "black"] | None,
    result: Literal["win", "draw", "loss"] | None,
    opponent: str | None,
    opening: str | None,
    time_class: str | None,
    rated: bool | None,
    since: dt.date | None,
    until: dt.date | None,
) -> list:
    """Las condiciones SQL de los filtros de RF-5.3.

    Salen aparte porque las necesitan dos consultas —la página de resultados y
    el total—, y si se escribieran dos veces acabarían diciendo cosas
    distintas.
    """
    conditions = []

    if username:
        if color == "white":
            conditions.append(is_white(username))
        elif color == "black":
            conditions.append(is_black(username))
        else:
            conditions.append(is_player(username))
        if result:
            conditions.append(outcome_of(username) == result)
        if opponent:
            # El rival es el del otro lado del tablero, así que depende de con
            # qué color jugó el usuario en cada partida.
            conditions.append(
                (is_white(username) & is_black(opponent))
                | (is_black(username) & is_white(opponent))
            )

    if opening:
        conditions.append(Game.opening_name.ilike(f"%{opening}%"))
    if time_class:
        conditions.append(Game.time_class == time_class)
    if rated is not None:
        conditions.append(Game.rated == rated)
    if since:
        conditions.append(Game.played_at >= dt.datetime.combine(since, dt.time.min))
    if until:
        # El día de `until` cuenta entero: quien filtra "hasta el 5" espera las
        # partidas del 5, no las de hasta su medianoche.
        conditions.append(
            Game.played_at < dt.datetime.combine(until, dt.time.min) + dt.timedelta(days=1)
        )
    return conditions


@router.get("/games", response_model=list[GameSummary])
async def list_games(
    session: Annotated[AsyncSession, Depends(get_session)],
    response: Response,
    username: str | None = None,
    color: Literal["white", "black"] | None = None,
    result: Literal["win", "draw", "loss"] | None = None,
    opponent: str | None = None,
    opening: str | None = None,
    time_class: str | None = None,
    rated: bool | None = None,
    since: dt.date | None = None,
    until: dt.date | None = None,
    limit: Annotated[int, Query(le=200, ge=1)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GameSummary]:
    """Listado filtrado de partidas (RF-5.3).

    **Tres de los filtros necesitan `username` y sin él se ignoran**: `color`,
    `result` y `opponent`. "Blancas", "ganadas" o "contra fulano" no significan
    nada sin decir de quién se habla; aplicarlos a medias daría un resultado
    plausible y equivocado, que es peor que no filtrar.

    `opening` busca por subcadena en el nombre de la apertura, para que
    "sicilian" traiga todas las sicilianas, no solo la variante exacta. El
    nombre es el de la tabla ECO propia (`lucia_core.openings`), así que las
    partidas que no empiezan en la posición estándar no salen con ningún
    filtro de apertura: no tienen apertura que nombrar.

    `since` y `until` son fechas inclusivas por los dos lados: `until` cubre el
    día entero, no hasta su medianoche.

    La cabecera **`X-Total-Count`** trae cuántas partidas cumplen los filtros,
    sin la paginación. Va en cabecera y no en el cuerpo para no envolver la
    lista: con ella la pantalla puede decir "25 de 324" en vez de solo el
    número de página, que no dice si el filtro dejó fuera media colección.
    """
    conditions = _filter_conditions(
        username=username,
        color=color,
        result=result,
        opponent=opponent,
        opening=opening,
        time_class=time_class,
        rated=rated,
        since=since,
        until=until,
    )
    query = (
        select(Game).where(*conditions).order_by(Game.played_at.desc()).limit(limit).offset(offset)
    )
    total = await session.scalar(select(func.count()).select_from(Game).where(*conditions))
    response.headers["X-Total-Count"] = str(total or 0)

    result_rows = await session.execute(query)
    return [GameSummary.model_validate(game) for game in result_rows.scalars().all()]


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(
    game_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> GameDetail:
    game = await session.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="no existe esa partida")
    return GameDetail.model_validate(game)

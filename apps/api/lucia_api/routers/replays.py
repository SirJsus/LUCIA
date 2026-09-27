"""GET /training/replays — desde qué errores propios se puede retomar una
partida contra el motor (RF-4.4).

Es **solo la lista**: retomar es abrir una partida de sparring desde esa
posición, y eso se pide a `POST /sparring/games` con su `origin`. Aquí no hay
nada que crear ni que guardar — la lista se deduce de los análisis que ya hay
cada vez que se pregunta (ver `services/replays.py`).

Desde el visor se puede retomar **cualquier** posición de cualquier partida
propia; esta lista es la versión curada, la que responde a "¿por dónde
empiezo?": los errores que más caros salieron, primero.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import resolved_username
from lucia_api.services.replays import count_replay_positions, replay_positions

router = APIRouter(prefix="/training", tags=["training"])

#: Cuántas posiciones se ofrecen. Es una lista para elegir, no un inventario:
#: con las veinte peores ya hay más trabajo del que cabe en una sesión.
DEFAULT_POSITIONS_LIMIT = 20
MAX_POSITIONS_LIMIT = 100


class ReplayPositionOut(BaseModel):
    """Un error propio desde el que se puede retomar la partida."""

    game_id: int
    ply: int
    """La jugada del error. Es lo que se manda como `origin.ply` al abrir la
    partida: retomar aquí es empezar en la posición **anterior** a esa jugada."""
    fen: str
    player_color: str
    """De qué color se jugaba la partida propia, con el mismo nombre que tiene
    al abrir la de sparring (`SparringGameCreate.player_color`): es el bando
    que la pantalla ofrece por defecto, aunque se pueda elegir el otro."""
    san: str
    classification: str
    win_percent_before: float
    win_percent_after: float
    """Lo que costó el error. Aquí sí viaja, al contrario que en un puzzle
    abierto: no hay nada que adivinar, y es lo que dice por cuál empezar."""
    opponent: str
    played_at: dt.datetime


class ReplayQueueOut(BaseModel):
    """La lista y cuántos errores hay, como la cola de puzzles y la de drills.

    El total no es `len(positions)`: la lista viene recortada a `limit`, así que
    sin él la pantalla enseñaba veinte de trescientos sin decir que había más
    (fila 102 del inventario de docs/07-coherencia-ui.md). Va en el cuerpo y no
    en una cabecera `X-Total-Count` como el listado de Partidas porque así lo
    traen las **dos** pestañas hermanas que también reparten una cola —puzzles
    y aperturas, `PuzzleQueueOut` y `DrillQueueOut`—, y es con ellas con las que
    se compara al cambiar de pestaña. El sparring no cuenta aquí: su listado es
    de partidas abiertas, no una cola, y `GET /sparring/games` devuelve la lista
    a secas.
    """

    positions: list[ReplayPositionOut]
    total: int


@router.get("/replays", response_model=ReplayQueueOut)
async def player_replay_positions(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_POSITIONS_LIMIT)] = DEFAULT_POSITIONS_LIMIT,
    username: str | None = None,
) -> ReplayQueueOut:
    """Los errores propios desde los que se puede retomar, del más caro al más
    barato, y cuántos hay en total."""
    player = resolved_username(username)
    rows = await replay_positions(session, player, limit)
    positions = [
        ReplayPositionOut(
            game_id=game.id,
            ply=move.ply,
            fen=move.fen_before,
            player_color=move.color,
            san=move.san,
            classification=move.classification,
            win_percent_before=move.win_percent_before,
            win_percent_after=move.win_percent_after,
            opponent=opponent,
            played_at=game.played_at,
        )
        for move, game, opponent in rows
    ]
    return ReplayQueueOut(positions=positions, total=await count_replay_positions(session, player))

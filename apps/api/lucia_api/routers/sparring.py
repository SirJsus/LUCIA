"""POST /sparring/games, GET /sparring/games, POST /sparring/games/{id}/moves
y POST /sparring/games/{id}/resign — jugar contra el motor con la fuerza
calibrada (RF-4.3).

El ciclo de la pantalla es el de estos endpoints: se abre una partida
eligiendo color y rival, se manda una jugada y en la misma respuesta vuelve la
del motor, y se abandona si uno quiere.

**Retomar una partida propia es este mismo ciclo** (RF-4.4): `POST
/sparring/games` acepta un `origin` —de qué partida y de qué jugada— y a
partir de ahí no hay nada distinto que hacer. Qué posiciones merecen retomarse
las lista `routers/replays.py`, que es solo una lista y no crea nada.

**Aquí el servidor valida las jugadas**, al revés que en el tablero de
análisis, donde quien sabe de reglas es chess.js y la API solo guarda el árbol
que le mandan. La diferencia es que aquí el servidor juega: para contestar
tiene que saber qué posición hay, y una jugada inventada por el navegador
dejaría la partida en una posición que el motor no reconocería.

Cada respuesta trae el estado completo de la partida —posición, jugadas,
resultado— y no el trocito que cambió: una partida de sparring cabe de sobra
en una respuesta, y así la pantalla nunca tiene que reconstruir nada.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

import chess
from fastapi import APIRouter, Depends, HTTPException, Query
from lucia_core.sparring import GameEnding, moves_san, to_pgn
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import SparringGame
from lucia_api.dependencies import resolved_username
from lucia_api.services.sparring import (
    SPARRING_ENGINE_NAMES,
    STOCKFISH_ELO_RANGE,
    create_game,
    current_board,
    get_game_position,
    list_games,
    missing_requirement,
    play_player_move,
    resign,
)

router = APIRouter(prefix="/sparring", tags=["sparring"])

#: Cuántas partidas devuelve el listado. Son pocas por naturaleza: se juegan
#: de una en una.
DEFAULT_GAMES_LIMIT = 20
MAX_GAMES_LIMIT = 100


class SparringGameOut(BaseModel):
    """Una partida de sparring entera: lo que hay en el tablero y cómo se llegó."""

    id: int
    player_color: str
    """"white" | "black": de qué color juega la persona."""
    engine: str
    engine_elo: int | None
    """Solo con Stockfish. `null` con Lc0, cuya fuerza es la de la red Maia
    cargada y no un número que se le pueda pedir."""
    origin_game_id: int | None
    origin_ply: int | None
    """De qué partida propia y de qué jugada se retomó esta (RF-4.4), o `null`
    si empieza desde el principio. Con ellos la pantalla puede decir de dónde
    salió y llevar de vuelta al visor. `origin_game_id` queda a `null` si esa
    partida se borró del historial: lo jugado aquí sigue valiendo, pero ya no
    hay adónde volver."""
    opponent_name: str
    """Cómo se llama el rival en pantalla y en el PGN: "Stockfish (1500)" o
    "Lc0 · Maia". Se compone aquí para que no haya dos versiones del nombre,
    una en la pantalla y otra en la partida exportada (criterio C-5)."""

    fen: str
    """La posición que hay ahora. Es lo que dibuja el tablero."""
    moves_san: list[str]
    """Las jugadas hechas, de las dos partes, para la lista de jugadas."""
    last_move_uci: str | None
    """La última jugada, para resaltar sus dos casillas. Normalmente la del
    motor, que es la que quien juega no ha visto hacerse."""
    is_player_turn: bool
    """Si toca mover a la persona. Con la partida terminada es siempre `false`:
    el tablero se queda quieto."""

    result: str | None
    """"1-0" | "0-1" | "1/2-1/2", o `null` mientras se juega."""
    termination: str | None
    """Por qué acabó (`lucia_core.sparring.Termination`): jaque mate, ahogado,
    material insuficiente, 50 jugadas, repetición o abandono. Va aparte del
    resultado porque "0-1" no distingue un mate de un abandono, y en un
    entrenamiento eso es justo lo que se quiere saber."""
    pgn: str
    """La partida en PGN. Es lo que la pantalla usa para abrirla como tablero
    de análisis (RF-6.6) y analizarla desde allí (RF-6.9), que es el camino por
    el que una partida de sparring se analiza sin entrar en las estadísticas."""

    created_at: dt.datetime
    updated_at: dt.datetime


class GamePositionIn(BaseModel):
    """Desde qué posición de qué partida propia se retoma (RF-4.4)."""

    game_id: int
    ply: int = Field(ge=0)
    """Jugadas ya hechas: 0 es el principio de la partida, y `ply` es la
    posición **anterior** a la jugada número `ply`. Retomar justo antes de un
    error es pedir el ply de ese error, que es como lo numera `AnalyzedMove`."""


class SparringGameCreate(BaseModel):
    player_color: str = Field(pattern="^(white|black)$")
    engine: str = Field(default="stockfish")
    engine_elo: int | None = None
    """Obligatorio con Stockfish, ignorado con Lc0. El rango se comprueba en
    el endpoint, contra `STOCKFISH_ELO_RANGE`."""
    origin: GamePositionIn | None = None
    """De dónde se retoma (RF-4.4). Sin esto la partida empieza en la posición
    inicial, que es el sparring de siempre (RF-4.3).

    Se manda **de qué partida y de qué jugada**, y no un FEN: la posición la
    deriva el servidor del PGN que ya tiene. Aceptar una posición cualquiera
    por HTTP sería empezar desde una posición inventada, que es RF-11.1 y está
    fuera del alcance de v1.0."""


class SparringMoveIn(BaseModel):
    uci: str
    """La jugada de la persona. La del motor vuelve en la misma respuesta."""


@router.post("/games", response_model=SparringGameOut, status_code=201)
async def start_sparring_game(
    body: SparringGameCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> SparringGameOut:
    """Abre una partida contra el motor, desde el principio o retomando una
    partida propia (RF-4.4). Si al motor le toca mover, ya ha movido cuando la
    respuesta llega."""
    if body.engine not in SPARRING_ENGINE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"motor desconocido: {body.engine!r}. Conocidos: {list(SPARRING_ENGINE_NAMES)}",
        )
    engine_elo = _validated_elo(body) if body.engine == "stockfish" else None
    try:
        origin = (
            await get_game_position(session, body.origin.game_id, body.origin.ply)
            if body.origin
            else None
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    missing_engine_requirement = missing_requirement(body.engine)
    if missing_engine_requirement is not None:
        raise HTTPException(
            status_code=422,
            detail=f"No se puede jugar contra {body.engine}: {missing_engine_requirement}",
        )

    game = await create_game(
        session,
        player_color=body.player_color,
        engine_name=body.engine,
        engine_elo=engine_elo,
        origin=origin,
    )
    return _to_out(game, resolved_username(username))


@router.get("/games", response_model=list[SparringGameOut])
async def list_sparring_games(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_GAMES_LIMIT)] = DEFAULT_GAMES_LIMIT,
    username: str | None = None,
) -> list[SparringGameOut]:
    """Las partidas jugadas, la de la última jugada primero. La pantalla
    distingue las vivas de las terminadas por `result`."""
    player_name = resolved_username(username)
    return [_to_out(game, player_name) for game in await list_games(session, limit)]


@router.get("/games/{game_id}", response_model=SparringGameOut)
async def get_sparring_game(
    game_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> SparringGameOut:
    """Retomar una partida: es lo que permite cerrar la pestaña a mitad y
    seguir después, porque el estado vive en la base y no en la pantalla."""
    return _to_out(await _get_game(session, game_id), resolved_username(username))


@router.post("/games/{game_id}/moves", response_model=SparringGameOut)
async def play_sparring_move(
    game_id: int,
    body: SparringMoveIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> SparringGameOut:
    """Juega una jugada y devuelve la partida con la respuesta del motor."""
    game = await _get_game(session, game_id)
    try:
        await play_player_move(session, game, body.uci)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _to_out(game, resolved_username(username))


@router.post("/games/{game_id}/resign", response_model=SparringGameOut)
async def resign_sparring_game(
    game_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> SparringGameOut:
    """Abandona la partida: gana el motor y la partida queda cerrada."""
    game = await _get_game(session, game_id)
    try:
        await resign(session, game)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _to_out(game, resolved_username(username))


def _validated_elo(body: SparringGameCreate) -> int:
    """El rango lo comprueba el endpoint y no el modelo porque solo aplica a
    Stockfish: con Lc0 el campo sobra, y un `Field(ge=..., le=...)` obligaría
    a mandar un número que nadie va a usar."""
    minimum, maximum = STOCKFISH_ELO_RANGE
    if body.engine_elo is None or not minimum <= body.engine_elo <= maximum:
        raise HTTPException(
            status_code=422,
            detail=f"Stockfish acepta un Elo entre {minimum} y {maximum}",
        )
    return body.engine_elo


async def _get_game(session: AsyncSession, game_id: int) -> SparringGame:
    game = await session.get(SparringGame, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="no existe esa partida de sparring")
    return game


def _opponent_name(game: SparringGame) -> str:
    """Cómo se llama el rival: el motor y, si la tiene, su fuerza pedida."""
    if game.engine == "stockfish":
        return f"Stockfish ({game.engine_elo})"
    return "Lc0 · Maia"


def _to_out(game: SparringGame, player_name: str) -> SparringGameOut:
    """La fila y las reglas, juntas en la forma que la pantalla dibuja.

    La posición y las jugadas en SAN se derivan de `moves_uci_json` en cada
    respuesta en vez de guardarse: así no hay dos versiones de la partida que
    puedan discrepar (ver la docstring de `SparringGame`).
    """
    board = current_board(game)
    opponent = _opponent_name(game)
    plays_white = game.player_color == "white"
    player_turn = board.turn == (chess.WHITE if plays_white else chess.BLACK)
    return SparringGameOut(
        id=game.id,
        player_color=game.player_color,
        engine=game.engine,
        engine_elo=game.engine_elo,
        origin_game_id=game.origin_game_id,
        origin_ply=game.origin_ply,
        opponent_name=opponent,
        fen=board.fen(),
        moves_san=moves_san(game.starting_fen, game.moves_uci_json),
        last_move_uci=game.moves_uci_json[-1] if game.moves_uci_json else None,
        is_player_turn=game.result is None and player_turn,
        result=game.result,
        termination=game.termination,
        pgn=to_pgn(
            game.starting_fen,
            game.moves_uci_json,
            white=player_name if plays_white else opponent,
            black=opponent if plays_white else player_name,
            ending=_stored_ending(game),
            date=game.created_at.strftime("%Y.%m.%d"),
        ),
        created_at=game.created_at,
        updated_at=game.updated_at,
    )


def _stored_ending(game: SparringGame) -> GameEnding | None:
    """Cómo acabó, leído de la fila y no vuelto a deducir del tablero: el
    abandono no se ve en la posición, y recalcularlo lo perdería."""
    if game.result is None or game.termination is None:
        return None
    return GameEnding(result=game.result, termination=game.termination)  # type: ignore[arg-type]

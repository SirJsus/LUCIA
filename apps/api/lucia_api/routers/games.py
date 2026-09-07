"""GET /games — listar y consultar partidas importadas (RF-5.3)."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Game

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


class GameDetail(GameSummary):
    pgn: str
    clocks_json: list | None


@router.get("/games", response_model=list[GameSummary])
async def list_games(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
    color: Literal["white", "black"] | None = None,
    time_class: str | None = None,
    rated: bool | None = None,
    limit: Annotated[int, Query(le=200, ge=1)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GameSummary]:
    """Filtros según RF-5.3. `color` sin `username` se ignora: "blancas" o
    "negras" no significa nada sin decir de quién."""
    query = select(Game).order_by(Game.played_at.desc()).limit(limit).offset(offset)
    if username:
        # Insensible a mayúsculas: chess.com da el perfil en minúsculas pero
        # el PGN conserva el casing original ("sirjsus" vs "SirJsus").
        is_white = func.lower(Game.white_username) == username.lower()
        is_black = func.lower(Game.black_username) == username.lower()
        if color == "white":
            query = query.where(is_white)
        elif color == "black":
            query = query.where(is_black)
        else:
            query = query.where(is_white | is_black)
    if time_class:
        query = query.where(Game.time_class == time_class)
    if rated is not None:
        query = query.where(Game.rated == rated)

    result = await session.execute(query)
    return [GameSummary.model_validate(game) for game in result.scalars().all()]


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(
    game_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> GameDetail:
    game = await session.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="no existe esa partida")
    return GameDetail.model_validate(game)

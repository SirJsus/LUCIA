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
    consulta = select(Game).order_by(Game.played_at.desc()).limit(limit).offset(offset)
    if username:
        # Insensible a mayúsculas: chess.com da el perfil en minúsculas pero
        # el PGN conserva el casing original ("sirjsus" vs "SirJsus").
        es_blancas = func.lower(Game.white_username) == username.lower()
        es_negras = func.lower(Game.black_username) == username.lower()
        if color == "white":
            consulta = consulta.where(es_blancas)
        elif color == "black":
            consulta = consulta.where(es_negras)
        else:
            consulta = consulta.where(es_blancas | es_negras)
    if time_class:
        consulta = consulta.where(Game.time_class == time_class)
    if rated is not None:
        consulta = consulta.where(Game.rated == rated)

    resultado = await session.execute(consulta)
    return [GameSummary.model_validate(g) for g in resultado.scalars().all()]


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(
    game_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> GameDetail:
    juego = await session.get(Game, game_id)
    if juego is None:
        raise HTTPException(status_code=404, detail="no existe esa partida")
    return GameDetail.model_validate(juego)

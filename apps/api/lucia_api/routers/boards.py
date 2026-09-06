"""CRUD de tableros de análisis (RF-6.1 a RF-6.5).

El árbol de variantes viaja como JSON opaco: la forma la define el front
(`apps/web/src/features/board/tree.ts`), que es quien tiene chess.js para
validar jugadas. Aquí solo se comprueba que sea un objeto y que el FEN raíz
sea legal, para no guardar un tablero que después no se pueda abrir.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any

import chess
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Board

router = APIRouter(tags=["boards"])


class BoardSummary(BaseModel):
    """Lo que hace falta para listar; sin el árbol, que puede ser grande."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    tags_json: list | None
    root_fen: str
    is_own_game: bool
    created_at: dt.datetime
    updated_at: dt.datetime


class BoardDetail(BoardSummary):
    tree_json: dict


class BoardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    root_fen: str = chess.STARTING_FEN
    tree_json: dict[str, Any] = Field(default_factory=dict)
    tags_json: list[str] | None = None
    is_own_game: bool = False


class BoardUpdate(BaseModel):
    """Todos los campos son opcionales: la UI autoguarda solo lo que cambió."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    tree_json: dict[str, Any] | None = None
    tags_json: list[str] | None = None
    is_own_game: bool | None = None


def _validar_fen(fen: str) -> None:
    try:
        chess.Board(fen)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"FEN inválido: {error}") from error


@router.get("/boards", response_model=list[BoardSummary])
async def list_boards(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BoardSummary]:
    resultado = await session.execute(
        select(Board).order_by(Board.updated_at.desc()).limit(limit).offset(offset)
    )
    return [BoardSummary.model_validate(b) for b in resultado.scalars().all()]


@router.post("/boards", response_model=BoardDetail, status_code=201)
async def create_board(
    body: BoardCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    _validar_fen(body.root_fen)
    tablero = Board(
        title=body.title,
        root_fen=body.root_fen,
        tree_json=body.tree_json,
        tags_json=body.tags_json,
        is_own_game=body.is_own_game,
    )
    session.add(tablero)
    await session.commit()
    return BoardDetail.model_validate(tablero)


@router.get("/boards/{board_id}", response_model=BoardDetail)
async def get_board(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    tablero = await session.get(Board, board_id)
    if tablero is None:
        raise HTTPException(status_code=404, detail="no existe ese tablero")
    return BoardDetail.model_validate(tablero)


@router.put("/boards/{board_id}", response_model=BoardDetail)
async def update_board(
    board_id: int,
    body: BoardUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BoardDetail:
    tablero = await session.get(Board, board_id)
    if tablero is None:
        raise HTTPException(status_code=404, detail="no existe ese tablero")

    if body.title is not None:
        tablero.title = body.title
    if body.tree_json is not None:
        tablero.tree_json = body.tree_json
    if body.tags_json is not None:
        tablero.tags_json = body.tags_json
    if body.is_own_game is not None:
        tablero.is_own_game = body.is_own_game
    tablero.updated_at = dt.datetime.now(dt.UTC)

    await session.commit()
    return BoardDetail.model_validate(tablero)


@router.delete("/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    tablero = await session.get(Board, board_id)
    if tablero is None:
        raise HTTPException(status_code=404, detail="no existe ese tablero")
    await session.delete(tablero)
    await session.commit()

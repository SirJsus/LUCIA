"""GET /stats/{username} — dashboard de estadísticas (RF-3.1 a RF-3.3)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.services.stats import PlayerStats, RecordSummary, get_player_stats
from lucia_api.settings import settings

router = APIRouter(tags=["stats"])


class RecordOut(BaseModel):
    wins: int
    draws: int
    losses: int
    total: int
    score_percent: float


class TimeClassStatsOut(BaseModel):
    time_class: str
    record: RecordOut
    current_rating: int | None


class MonthlyCountOut(BaseModel):
    year: int
    month: int
    games: int


class OpeningStatsOut(BaseModel):
    opening: str
    color: str
    record: RecordOut
    average_accuracy: float | None


class PhaseStatsOut(BaseModel):
    phase: str
    moves: int
    average_accuracy: float
    average_win_percent_lost: float
    blunders: int


class PlayerStatsOut(BaseModel):
    username: str
    total_games: int
    overall: RecordOut
    by_time_class: list[TimeClassStatsOut]
    by_month: list[MonthlyCountOut]
    by_opening: list[OpeningStatsOut]
    by_phase: list[PhaseStatsOut]
    analyzed_games: int
    average_accuracy: float | None


def _record_out(record: RecordSummary) -> RecordOut:
    # `total` y `score_percent` son propiedades calculadas, no campos, así que
    # se copian a mano en vez de con `model_validate`.
    return RecordOut(
        wins=record.wins,
        draws=record.draws,
        losses=record.losses,
        total=record.total,
        score_percent=record.score_percent,
    )


def _stats_out(stats: PlayerStats) -> PlayerStatsOut:
    return PlayerStatsOut(
        username=stats.username,
        total_games=stats.total_games,
        overall=_record_out(stats.overall),
        by_time_class=[
            TimeClassStatsOut(
                time_class=item.time_class,
                record=_record_out(item.record),
                current_rating=item.current_rating,
            )
            for item in stats.by_time_class
        ],
        by_month=[
            MonthlyCountOut(year=item.year, month=item.month, games=item.games)
            for item in stats.by_month
        ],
        by_opening=[
            OpeningStatsOut(
                opening=item.opening,
                color=item.color,
                record=_record_out(item.record),
                average_accuracy=item.average_accuracy,
            )
            for item in stats.by_opening
        ],
        by_phase=[
            PhaseStatsOut(
                phase=item.phase,
                moves=item.moves,
                average_accuracy=item.average_accuracy,
                average_win_percent_lost=item.average_win_percent_lost,
                blunders=item.blunders,
            )
            for item in stats.by_phase
        ],
        analyzed_games=stats.analyzed_games,
        average_accuracy=stats.average_accuracy,
    )


@router.get("/stats", response_model=PlayerStatsOut)
async def player_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
    limit_openings: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PlayerStatsOut:
    """Estadísticas del jugador indicado, o del de `CHESSCOM_USERNAME` si se
    omite. Se pide el nombre porque la base guarda partidas de ambos bandos:
    sin saber quién es "yo", un marcador de victorias no significa nada."""
    jugador = username or settings.chesscom_username
    if not jugador:
        raise HTTPException(
            status_code=422,
            detail="indica un username, o configura CHESSCOM_USERNAME en .env",
        )
    return _stats_out(await get_player_stats(session, jugador, limit_openings))

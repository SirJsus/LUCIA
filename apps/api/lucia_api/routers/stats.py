"""GET /stats/{username} — dashboard de estadísticas (RF-3.1 a RF-3.5)."""

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
    eco: str | None
    """Código ECO de la apertura ("B90"), de la tabla propia: chess.com no lo
    da."""
    color: str
    record: RecordOut
    average_accuracy: float | None
    average_opening_exit_win_percent: float | None
    """Con qué posición se sale de la apertura, en probabilidad de victoria del
    jugador (RF-3.2)."""


class MistakeTypeStatsOut(BaseModel):
    """Cuántos errores de cada tipo y por qué (RF-3.4)."""

    mistake_type: str
    """"time" (con el reloj encima), "tactical" (había una captura o un jaque
    que ver), "endgame" (técnica de final) o "positional" (el plan)."""
    mistakes: int
    blunders: int


class TimeBucketStatsOut(BaseModel):
    """Calidad de juego con un reloj determinado (RF-3.5)."""

    max_seconds_left: float | None
    """Techo del tramo en segundos, o `null` para el tramo holgado."""
    moves: int
    average_accuracy: float
    mistakes: int
    blunders: int


class TimeTroubleOut(BaseModel):
    games_in_time_trouble: int
    analyzed_games_with_clocks: int
    share_of_games: float


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
    by_mistake_type: list[MistakeTypeStatsOut]
    by_time_left: list[TimeBucketStatsOut]
    time_trouble: TimeTroubleOut | None
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
                eco=item.eco,
                color=item.color,
                record=_record_out(item.record),
                average_accuracy=item.average_accuracy,
                average_opening_exit_win_percent=item.average_opening_exit_win_percent,
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
        by_mistake_type=[
            MistakeTypeStatsOut(
                mistake_type=item.mistake_type, mistakes=item.mistakes, blunders=item.blunders
            )
            for item in stats.by_mistake_type
        ],
        by_time_left=[
            TimeBucketStatsOut(
                max_seconds_left=item.max_seconds_left,
                moves=item.moves,
                average_accuracy=item.average_accuracy,
                mistakes=item.mistakes,
                blunders=item.blunders,
            )
            for item in stats.by_time_left
        ],
        time_trouble=(
            TimeTroubleOut(
                games_in_time_trouble=stats.time_trouble.games_in_time_trouble,
                analyzed_games_with_clocks=stats.time_trouble.analyzed_games_with_clocks,
                share_of_games=stats.time_trouble.share_of_games,
            )
            if stats.time_trouble is not None
            else None
        ),
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
    resolved_username = username or settings.chesscom_username
    if not resolved_username:
        raise HTTPException(
            status_code=422,
            detail="indica un username, o configura CHESSCOM_USERNAME en .env",
        )
    return _stats_out(await get_player_stats(session, resolved_username, limit_openings))

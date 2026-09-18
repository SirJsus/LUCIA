"""GET /stats/{username} — dashboard de estadísticas (RF-3.1 a RF-3.7)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import resolved_username
from lucia_api.services.stats import PlayerStats, RecordSummary, TrendsSummary, get_player_stats

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


class MistakeRateOut(BaseModel):
    mistake_type: str
    per_hundred_moves: float


class MonthlyQualityOut(BaseModel):
    """Cómo se jugó en un mes (RF-3.7)."""

    year: int
    month: int
    analyzed_games: int
    moves: int
    """Jugadas del jugador sobre las que se calculó el mes: dice si el punto es
    sólido o son dos partidas sueltas."""
    average_accuracy: float
    blunders_per_hundred_moves: float
    mistakes_per_hundred_moves: list[MistakeRateOut]
    """Un valor por tipo de error, siempre los cuatro y siempre en el mismo
    orden, para que la serie no cambie de categorías de un mes a otro. Va por
    cada cien jugadas y no en recuento crudo: si no, la línea subiría al jugar
    más partidas en vez de al jugar peor."""
    rating: int | None
    """Rating de cierre del mes en `TrendsOut.rating_time_class`."""


class TrendChangeOut(BaseModel):
    """El último mes frente a los anteriores (RF-3.7)."""

    baseline_months: int
    """Contra cuántos meses anteriores se comparó."""
    accuracy_change: float
    mistake_rate_change: float
    """Subir es empeorar, al revés que la precisión."""


class TrendsOut(BaseModel):
    """Evolución del juego en el tiempo (RF-3.7), lo que el dashboard dibuja
    en "Cómo evolucionas"."""

    by_month: list[MonthlyQualityOut]
    """De más antiguo a más reciente, y solo los meses con alguna partida
    analizada: la lista vacía significa "todavía no hay nada que comparar"."""
    change: TrendChangeOut | None
    """`None` cuando solo hay un mes: no hay con qué compararlo."""
    rating_time_class: str | None
    """A qué control de tiempo pertenece `MonthlyQualityOut.rating`: el más
    jugado. `None` si no hay ninguno del que hablar —solo partidas importadas
    de un PGN sin control—, y entonces la interfaz omite la serie entera en
    vez de rotularla con un hueco."""


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
    trends: TrendsOut
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


def _trends_out(trends: TrendsSummary) -> TrendsOut:
    # `MoveQuality` se aplana aquí: en el núcleo es un objeto aparte porque
    # sirve para cualquier tramo, pero la interfaz dibuja una fila por mes.
    return TrendsOut(
        by_month=[
            MonthlyQualityOut(
                year=item.year,
                month=item.month,
                analyzed_games=item.analyzed_games,
                moves=item.quality.moves,
                average_accuracy=item.quality.average_accuracy,
                blunders_per_hundred_moves=item.quality.blunders_per_hundred_moves,
                mistakes_per_hundred_moves=[
                    MistakeRateOut(
                        mistake_type=rate.mistake_type, per_hundred_moves=rate.per_hundred_moves
                    )
                    for rate in item.quality.mistakes_per_hundred_moves
                ],
                rating=item.rating,
            )
            for item in trends.by_month
        ],
        change=(
            TrendChangeOut(
                baseline_months=trends.change.baseline_periods,
                accuracy_change=trends.change.accuracy_change,
                mistake_rate_change=trends.change.mistake_rate_change,
            )
            if trends.change is not None
            else None
        ),
        rating_time_class=trends.rating_time_class,
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
        trends=_trends_out(stats.trends),
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
    return _stats_out(await get_player_stats(session, resolved_username(username), limit_openings))

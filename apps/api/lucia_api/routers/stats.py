"""GET /stats/{username} — dashboard de estadísticas (RF-3.1 a RF-3.7)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import resolved_username
from lucia_api.services.stats import get_player_stats

router = APIRouter(tags=["stats"])


class StatsOut(BaseModel):
    """Base común de las respuestas de esta pantalla.

    `from_attributes` es lo único que aporta, y es lo que permite armar cada
    modelo directamente desde su `dataclass` —de `services/stats.py` o de
    `lucia_core.insights`— con `model_validate`, en vez de copiar campo a
    campo. Los nombres coinciden a propósito, y las propiedades calculadas
    (`total`, `score_percent`, `share_of_games`) entran igual que los campos.
    """

    model_config = ConfigDict(from_attributes=True)


class RecordOut(StatsOut):
    wins: int
    draws: int
    losses: int
    total: int
    score_percent: float


class TimeClassStatsOut(StatsOut):
    time_class: str
    record: RecordOut
    current_rating: int | None


class MonthlyCountOut(StatsOut):
    year: int
    month: int
    games: int


class OpeningStatsOut(StatsOut):
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


class MistakeTypeStatsOut(StatsOut):
    """Cuántos errores de cada tipo y por qué (RF-3.4)."""

    mistake_type: str
    """"time" (con el reloj encima), "tactical" (había una captura o un jaque
    que ver), "endgame" (técnica de final) o "positional" (el plan)."""
    mistakes: int
    blunders: int


class TimeBucketStatsOut(StatsOut):
    """Calidad de juego con un reloj determinado (RF-3.5)."""

    max_seconds_left: float | None
    """Techo del tramo en segundos, o `null` para el tramo holgado."""
    moves: int
    average_accuracy: float
    mistakes: int
    blunders: int


class TimeTroubleOut(StatsOut):
    games_in_time_trouble: int
    analyzed_games_with_clocks: int
    share_of_games: float


class PhaseStatsOut(StatsOut):
    phase: str
    moves: int
    average_accuracy: float
    average_win_percent_lost: float
    blunders: int


class MistakeRateOut(StatsOut):
    mistake_type: str
    per_hundred_moves: float


class MonthlyQualityOut(StatsOut):
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

    @model_validator(mode="before")
    @classmethod
    def _flatten_quality(cls, monthly: Any) -> Any:
        """`MoveQuality` se aplana aquí: en el núcleo es un objeto aparte
        porque sirve para cualquier tramo, pero la interfaz dibuja una fila
        por mes."""
        quality = getattr(monthly, "quality", None)
        return monthly if quality is None else asdict(monthly) | asdict(quality)


class TrendChangeOut(StatsOut):
    """El último mes frente a los anteriores (RF-3.7)."""

    baseline_months: int = Field(validation_alias="baseline_periods")
    """Contra cuántos meses anteriores se comparó. En el núcleo el tramo es
    genérico (`TrendChange.baseline_periods`); aquí siempre es un mes."""
    accuracy_change: float
    mistake_rate_change: float
    """Subir es empeorar, al revés que la precisión."""


class TrendsOut(StatsOut):
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


class PlayerStatsOut(StatsOut):
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


@router.get("/stats", response_model=PlayerStatsOut)
async def player_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
    limit_openings: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PlayerStatsOut:
    """Estadísticas del jugador indicado, o del de `CHESSCOM_USERNAME` si se
    omite. Se pide el nombre porque la base guarda partidas de ambos bandos:
    sin saber quién es "yo", un marcador de victorias no significa nada."""
    stats = await get_player_stats(session, resolved_username(username), limit_openings)
    return PlayerStatsOut.model_validate(stats)

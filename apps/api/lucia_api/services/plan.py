"""Plan de entrenamiento semanal (RF-4.5): juntar lo que se sabe del jugador
con lo que hay para entrenar.

Este módulo **solo recoge números**; qué es una debilidad y qué se hace con
ella lo decide `lucia_core.plan`, que es puro. De un lado llegan las
estadísticas de RF-3 —fase donde se pierde ventaja (RF-3.3), tipo de error más
frecuente (RF-3.4), aperturas que cuestan puntos (RF-3.2), apuros de reloj
(RF-3.5) y tendencia de precisión (RF-3.7)—; del otro, cuánto material hay en
cada forma de entrenar y cuánto se ha hecho ya esta semana.

**Nada se guarda.** El plan se recalcula en cada visita y su avance sale de lo
que ya está fechado en la base: `puzzles.last_reviewed_at`,
`opening_drills.last_reviewed_at` y `sparring_games.created_at`. No hay tabla
ni estado propio, por lo mismo que la lista de re-jugar (ADR-0020) y los
patrones (ADR-0008): un plan congelado el lunes sería una copia que envejece
en cuanto se analiza una partida más.

Lo consume `routers/plan.py`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from lucia_core.drills import points_lost
from lucia_core.plan import (
    MAX_WEEKLY_TARGETS,
    PlanTask,
    TrainingTaskKind,
    Weakness,
    build_weekly_tasks,
    detect_weaknesses,
    week_start,
)
from sqlalchemy import ColumnExpressionArgument, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.base import Base
from lucia_api.db.models import OpeningDrill, Puzzle, SparringGame
from lucia_api.services.replays import replay_positions
from lucia_api.services.stats import MAX_OPENINGS_CONSIDERED, PlayerStats, get_player_stats

#: Cuántas posiciones de re-jugar se consideran material disponible. Es el
#: mismo tope que ofrece su propia pantalla: más allá no son "las peores".
MAX_REPLAY_POSITIONS_CONSIDERED = 20


@dataclass
class WeeklyPlan:
    """El plan de la semana y de dónde sale."""

    week_start: dt.datetime
    weaknesses: list[Weakness]
    tasks: list[PlanTask]
    analyzed_games: int
    """Sobre cuántas partidas analizadas se ha hecho el diagnóstico. Sin
    análisis no hay debilidades que detectar, y la pantalla tiene que poder
    distinguir "no tienes problemas" de "todavía no lo sé"."""


async def weekly_training_plan(
    session: AsyncSession, username: str, now: dt.datetime
) -> WeeklyPlan:
    """El plan de esta semana, deducido de lo que ya se sabe."""
    stats = await get_player_stats(session, username, limit_openings=MAX_OPENINGS_CONSIDERED)
    monday = week_start(now)
    detected_weaknesses = _weaknesses_from_stats(stats)
    return WeeklyPlan(
        week_start=monday,
        weaknesses=detected_weaknesses,
        tasks=build_weekly_tasks(
            detected_weaknesses,
            available_material=await _available_material(session, username, monday),
            done_this_week=await _done_since(session, monday),
        ),
        analyzed_games=stats.analyzed_games,
    )


def _weaknesses_from_stats(stats: PlayerStats) -> list[Weakness]:
    """Las estadísticas de RF-3, traducidas a los números que espera el núcleo.

    Es la única traducción que hace este módulo, y por eso vive aparte: lo que
    llega de `get_player_stats` son cinco formas distintas de contar, y lo que
    `lucia_core.plan` necesita son cinco números comparables con su umbral.
    """
    total_mistakes = sum(count.mistakes for count in stats.by_mistake_type)
    return detect_weaknesses(
        average_win_percent_lost_by_phase={
            phase.phase: phase.average_win_percent_lost for phase in stats.by_phase
        },
        mistake_share_by_type={
            count.mistake_type: count.mistakes / total_mistakes * 100
            for count in stats.by_mistake_type
        }
        if total_mistakes
        else {},
        opening_points_lost=[
            (
                opening.opening,
                opening.color,
                points_lost(opening.record.total, opening.record.score_percent),
            )
            for opening in stats.by_opening
        ],
        time_trouble_share=stats.time_trouble.share_of_games if stats.time_trouble else 0.0,
        accuracy_change=stats.trends.change.accuracy_change if stats.trends.change else None,
    )


async def _available_material(
    session: AsyncSession, username: str, monday: dt.datetime
) -> dict[TrainingTaskKind, int]:
    """Cuánto material hay de cada cosa, que es el techo real de cada tarea.

    Puzzles y líneas cuentan los que **vencen esta semana**, no todos los que
    existen: repasar antes de tiempo no es entrenar, es adelantar trabajo que
    el SM-2 ya había colocado. Sparring no tiene material que agotar —siempre
    se puede jugar otra—, así que su techo es el objetivo semanal.
    """
    end_of_week = monday + dt.timedelta(days=7)
    return {
        "puzzles": await _count_rows(session, Puzzle, Puzzle.due_at < end_of_week),
        "drills": await _count_rows(session, OpeningDrill, OpeningDrill.due_at < end_of_week),
        "replays": len(await replay_positions(session, username, MAX_REPLAY_POSITIONS_CONSIDERED)),
        "sparring": MAX_WEEKLY_TARGETS["sparring"],
    }


async def _done_since(session: AsyncSession, monday: dt.datetime) -> dict[TrainingTaskKind, int]:
    """Qué se ha hecho ya esta semana, leído de las fechas que la base ya
    guarda. Nadie marca nada a mano: el avance es lo que se hizo."""
    played_this_week = SparringGame.created_at >= monday
    return {
        "puzzles": await _count_rows(session, Puzzle, Puzzle.last_reviewed_at >= monday),
        "drills": await _count_rows(session, OpeningDrill, OpeningDrill.last_reviewed_at >= monday),
        # Una posición re-jugada es una partida de sparring con procedencia
        # (RF-4.4); una de sparring a secas, una sin ella.
        "replays": await _count_rows(
            session, SparringGame, played_this_week, SparringGame.origin_game_id.is_not(None)
        ),
        "sparring": await _count_rows(
            session, SparringGame, played_this_week, SparringGame.origin_game_id.is_(None)
        ),
    }


async def _count_rows(
    session: AsyncSession, model: type[Base], *conditions: ColumnExpressionArgument[bool]
) -> int:
    """Cuántas filas de `model` cumplen las condiciones."""
    return await session.scalar(select(func.count()).select_from(model).where(*conditions)) or 0

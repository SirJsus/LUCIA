"""GET /training/plan — el plan de entrenamiento de la semana (RF-4.5).

Un solo endpoint y de solo lectura, porque **el plan no se guarda**: se deduce
en cada visita de las estadísticas (RF-3) y de las colas de entrenamiento
(RF-4), y su avance sale de lo que ya está fechado en la base. No hay nada que
crear ni que marcar — hacer los deberes es usar las otras pantallas, y el plan
se entera solo.

Cada tarea viaja **con las debilidades que la piden**, y no suelta: el
requerimiento dice "generado a partir de las debilidades detectadas", así que
poder ver de dónde sale cada deber es parte de lo que se entrega. Traducir esos
números a una frase es cosa de la pantalla.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import resolved_username
from lucia_api.services.plan import weekly_training_plan

router = APIRouter(prefix="/training", tags=["training"])


class WeaknessOut(BaseModel):
    """Algo que se está haciendo mal, con su número y de dónde sale."""

    model_config = ConfigDict(from_attributes=True)

    kind: str
    """"phase" | "mistake_type" | "opening" | "time_trouble" | "accuracy_trend".
    Cada una viene de un requerimiento de RF-3 distinto y se cuenta de otra
    manera, así que la pantalla necesita saber cuál es para redactarla."""
    subject: str
    """La fase, el tipo de error o el nombre de la apertura. Vacío en las que
    no se refieren a nada en concreto (la tendencia, los apuros de reloj)."""
    magnitude: float
    """Cuánto de esto hay, **en la unidad de su clase**: puntos de probabilidad
    de victoria por jugada en una fase, porcentaje de los errores en un tipo,
    puntos de marcador en una apertura, porcentaje de partidas con apuros,
    puntos de precisión perdidos en la tendencia. No es comparable entre
    clases: sirve para ordenar, no para restar."""
    color: str
    """Con qué bando duele, solo en las aperturas. Vacío en las demás."""


class PlanTaskOut(BaseModel):
    """Un deber de la semana: qué entrenar, cuánto y por qué."""

    model_config = ConfigDict(from_attributes=True)

    kind: str
    """"puzzles" | "drills" | "replays" | "sparring": a qué pantalla lleva."""
    weekly_target: int
    """Cuántos hacer de aquí al domingo. Nunca más de los que hay."""
    done_this_week: int
    """Cuántos van hechos desde el lunes. Nadie lo marca a mano: sale de las
    fechas que la base ya guarda."""
    weaknesses: list[WeaknessOut]
    """Las debilidades que piden esta tarea, en el mismo orden de la lista de
    arriba. Más de una cuando varias apuntan al mismo entrenamiento. Se llaman
    igual que las de `WeeklyPlanOut` porque son las mismas, filtradas: estas son
    las que apuntan a esta tarea."""


class WeeklyPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_start: dt.datetime
    """El lunes de esta semana. El avance se cuenta desde aquí."""
    weaknesses: list[WeaknessOut]
    """Todas las detectadas, en orden de por dónde conviene empezar — un orden
    fijo por clase, no por `magnitude`, que no es comparable entre ellas (ver
    `lucia_core.plan.detect_weaknesses`). Incluye las que no dan tarea. Vacío significa
    que no se ha encontrado nada que arreglar, no que falte por mirar: para eso
    está `analyzed_games`."""
    tasks: list[PlanTaskOut]
    analyzed_games: int
    """Sobre cuántas partidas analizadas se hizo el diagnóstico. Con cero no
    hay debilidades que detectar, y la pantalla dice que hay que analizar en
    vez de felicitar por un plan vacío."""


@router.get("/plan", response_model=WeeklyPlanOut)
async def player_weekly_plan(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> WeeklyPlanOut:
    """El plan de esta semana: qué falla y qué hacer al respecto."""
    plan = await weekly_training_plan(session, resolved_username(username), dt.datetime.now(dt.UTC))
    return WeeklyPlanOut.model_validate(plan)

"""Repaso espaciado de los ejercicios: la cola de lo que toca y el apunte de
cómo fue (RF-4.1 y RF-4.2).

Un drill de apertura se repasa **como se repasa un puzzle**: mismo algoritmo
(SM-2, `lucia_core.training`), mismo estado en la base (el mixin
`SpacedRepetition`) y, por tanto, misma cola y mismo apunte. Aquí viven los
dos, una sola vez, para que no puedan divergir — que es justo lo que había
pasado: la cola de los drills anunciaba como "próximo repaso" el vencimiento
más antiguo de todos, incluidos los ya vencidos, y lo mandaba sin zona
horaria, así que la pantalla enseñaba un día que no era.

Lo que cambia de un ejercicio a otro —de dónde sale, qué se le pregunta al
usuario y qué cuenta como acertar— vive en `services/training.py` y en
`services/drills.py`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from lucia_core.training import ReviewGrade, SpacedRepetitionState, next_review
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import SpacedRepetition

#: Cuántos ejercicios se reparten de una vez. Una sesión de entrenamiento se
#: hace de unos pocos; pedir los cuatrocientos que puede haber vencidos solo
#: serviría para que la pantalla tardara en abrirse.
DEFAULT_QUEUE_LIMIT = 20
MAX_QUEUE_LIMIT = 100


def utc_now() -> dt.datetime:
    """Ahora, en UTC, que es como se guardan todas las fechas."""
    return dt.datetime.now(dt.UTC)


@dataclass(frozen=True)
class ReviewQueue[ItemT: SpacedRepetition]:
    """Lo que toca repasar y el contexto para saber qué se está viendo."""

    items: list[ItemT]
    """Los que tocan ahora, del más atrasado al más reciente."""
    due: int
    """Cuántos tocan en total, que pueden ser más de los que caben en la tanda."""
    total: int
    next_due_at: dt.datetime | None
    """Cuándo vuelve a haber trabajo si ahora no queda nada. `None` si no hay
    ningún ejercicio todavía; sin esto, una pantalla vacía no sabría distinguir
    "no has generado nada" de "hoy ya terminaste" (criterio C-3)."""


async def review_queue[ItemT: SpacedRepetition](
    session: AsyncSession, model: type[ItemT], now: dt.datetime, limit: int
) -> ReviewQueue[ItemT]:
    """La cola de repaso de un tipo de ejercicio, del más atrasado al más
    reciente.

    Se ordena por vencimiento y no al azar: lo más atrasado primero es lo que
    hace que la cola se vacíe en vez de crecer.
    """
    due_items = list(
        (
            await session.execute(
                select(model).where(model.due_at <= now).order_by(model.due_at).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    total, due, next_due_at = (
        await session.execute(
            select(
                func.count(model.due_at),
                func.count(model.due_at).filter(model.due_at <= now),
                # El próximo repaso es el primero que **todavía no** vence: con
                # el mínimo absoluto, una cola vacía anunciaría como "próximo"
                # algo ya vencido.
                func.min(model.due_at).filter(model.due_at > now),
            )
        )
    ).one()
    return ReviewQueue(items=due_items, due=due, total=total, next_due_at=_as_utc(next_due_at))


def _as_utc(moment: dt.datetime | None) -> dt.datetime | None:
    """SQLite devuelve las fechas sin zona horaria aunque la columna la
    declare; se marcan como UTC, que es como se escribieron, para que el
    cliente no las lea en su hora local."""
    if moment is None:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=dt.UTC)


def record_review(item: SpacedRepetition, grade: ReviewGrade, now: dt.datetime) -> None:
    """Guarda en el ejercicio el estado que devuelve SM-2 y cuándo vuelve.

    El próximo vencimiento se cuenta desde **ahora** y no desde el anterior:
    repasar con retraso no encadena retrasos.
    """
    state_after_review = next_review(
        SpacedRepetitionState(
            repetitions=item.repetitions,
            interval_days=item.interval_days,
            ease_factor=item.ease_factor,
        ),
        grade,
    )
    item.repetitions = state_after_review.repetitions
    item.interval_days = state_after_review.interval_days
    item.ease_factor = state_after_review.ease_factor
    item.last_reviewed_at = now
    item.due_at = now + dt.timedelta(days=state_after_review.interval_days)

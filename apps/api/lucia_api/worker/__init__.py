"""Cola de análisis en background (RF-2.4): un `asyncio.Queue` en proceso,
sin Redis (ver ADR-0001/0005 y docs/04-stack-tecnologico.md — se extrae a
`arq` + Redis si hace falta escalar). Un único consumidor procesa un análisis
a la vez; el progreso se publica a quien esté escuchando por WebSocket.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections import defaultdict
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from lucia_api.db.base import async_session_factory
from lucia_api.db.models import Analysis, Game
from lucia_api.services.analysis import run_analysis

Event = dict[str, object]


class AnalysisWorker:
    """`session_factory` es inyectable (por defecto, la sesión real de la
    app) para que los tests puedan apuntarlo a una base temporal sin tocar
    `data/lucia.db` — ver `apps/api/tests/conftest.py`."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession]
        | Callable[[], AsyncSession] = async_session_factory,
    ) -> None:
        self._session_factory = session_factory
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._subscribers: dict[int, list[asyncio.Queue[Event]]] = defaultdict(list)
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def enqueue(self, analysis_id: int) -> None:
        await self._queue.put(analysis_id)

    def subscribe(self, analysis_id: int) -> asyncio.Queue[Event]:
        """Un WebSocket llama esto para recibir eventos de progreso."""
        cola: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[analysis_id].append(cola)
        return cola

    def unsubscribe(self, analysis_id: int, cola: asyncio.Queue[Event]) -> None:
        with contextlib.suppress(ValueError):
            self._subscribers[analysis_id].remove(cola)
        if not self._subscribers[analysis_id]:
            self._subscribers.pop(analysis_id, None)

    async def _publish(self, analysis_id: int, evento: Event) -> None:
        for cola in self._subscribers.get(analysis_id, []):
            await cola.put(evento)

    async def _consume(self) -> None:
        while True:
            analysis_id = await self._queue.get()
            try:
                await self._process(analysis_id)
            finally:
                self._queue.task_done()

    async def _process(self, analysis_id: int) -> None:
        async with self._session_factory() as session:
            analysis = await session.get(Analysis, analysis_id)
            if analysis is None:
                return  # se borró entre encolar y procesar; nada que hacer
            game = await session.get(Game, analysis.game_id)
            if game is None:
                analysis.status = "error"
                analysis.error = "la partida ya no existe"
                await session.commit()
                await self._publish(analysis_id, {"status": "error", "error": analysis.error})
                return

            async def progreso(ply: int, total: int) -> None:
                await self._publish(analysis_id, {"status": "running", "ply": ply, "total": total})

            await run_analysis(session, analysis, game, on_progress=progreso)
            await self._publish(analysis_id, {"status": analysis.status, "error": analysis.error})

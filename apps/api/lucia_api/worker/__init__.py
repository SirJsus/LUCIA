"""Cola de análisis en background (RF-2.4, RF-6.9): un `asyncio.Queue` en proceso,
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
        subscriber_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[analysis_id].append(subscriber_queue)
        return subscriber_queue

    def unsubscribe(self, analysis_id: int, subscriber_queue: asyncio.Queue[Event]) -> None:
        with contextlib.suppress(ValueError):
            self._subscribers[analysis_id].remove(subscriber_queue)
        if not self._subscribers[analysis_id]:
            self._subscribers.pop(analysis_id, None)

    async def _publish(self, analysis_id: int, event: Event) -> None:
        for subscriber_queue in self._subscribers.get(analysis_id, []):
            await subscriber_queue.put(event)

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
            pgn = await self._load_pgn_to_analyze(session, analysis)
            if pgn is None:
                analysis.status = "error"
                analysis.error = "lo que había que analizar ya no existe"
                await session.commit()
                await self._publish(analysis_id, {"status": "error", "error": analysis.error})
                return

            async def publish_progress(ply: int, total: int) -> None:
                await self._publish(analysis_id, {"status": "running", "ply": ply, "total": total})

            await run_analysis(session, analysis, pgn, on_progress=publish_progress)
            await self._publish(analysis_id, {"status": analysis.status, "error": analysis.error})

    async def _load_pgn_to_analyze(self, session: AsyncSession, analysis: Analysis) -> str | None:
        """Las jugadas que hay que analizar, vengan de donde vengan.

        Un análisis de tablero (RF-6.9) trae su PGN consigo —lo mandó el
        front al pedirlo, porque el árbol lo interpreta chess.js y no la
        API—; uno de partida lo lee de `games.pgn`, que no cambia. `None` si
        la partida se borró entre encolar y procesar.
        """
        if analysis.analyzed_pgn is not None:
            return analysis.analyzed_pgn
        game = await session.get(Game, analysis.game_id)
        return game.pgn if game is not None else None

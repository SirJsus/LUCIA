"""Dependencias de FastAPI compartidas entre routers (fuera de las de `db/`,
que viven junto al motor y la sesión)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from lucia_chesscom import ChessComClient

from .settings import settings
from .worker import AnalysisWorker


async def get_chesscom_client() -> AsyncIterator[ChessComClient]:
    """Un `ChessComClient` por request, cerrado al terminar. En tests se
    reemplaza con `app.dependency_overrides` por un cliente falso."""
    async with ChessComClient(user_agent=settings.chesscom_user_agent) as client:
        yield client


def get_worker(request: Request) -> AnalysisWorker:
    """El `AnalysisWorker` vive en `app.state`, creado en el `lifespan` de
    `main.py` (uno por proceso, no uno por request)."""
    return request.app.state.worker

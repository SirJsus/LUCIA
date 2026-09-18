from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import __version__
from .routers import (
    analysis,
    boards,
    engines,
    games,
    health,
    pgn_import,
    repertoire,
    stats,
    sync,
)
from .worker import AnalysisWorker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # `hasattr` en vez de crear siempre uno nuevo: así los tests pueden fijar
    # `app.state.worker` antes de arrancar (p. ej. con una sesión de BD
    # temporal) y el lifespan respeta esa instancia en vez de reemplazarla.
    if not hasattr(app.state, "worker"):
        app.state.worker = AnalysisWorker()
    app.state.worker.start()
    yield
    await app.state.worker.stop()


app = FastAPI(
    title="L.U.C.I.A. API",
    description="Logic & Ultimate Chess Insight Algorithm",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(sync.router)
app.include_router(games.router)
app.include_router(pgn_import.router)
app.include_router(analysis.router)
app.include_router(engines.router)
app.include_router(stats.router)
app.include_router(boards.router)
app.include_router(repertoire.router)

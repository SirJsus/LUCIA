"""La aplicación FastAPI: monta los routers y levanta el worker de análisis.

Es el único sitio donde se sabe qué endpoints existen —cada router trae los
suyos, con su RF en la cabecera— y quien pone en `app.state.worker` la cola en
proceso que atiende los análisis de partida (RF-2.4) y de tablero (RF-6.9),
para que los routers la alcancen sin variables globales. De aquí sale también
el `openapi.json` que `scripts/export-openapi.py` vuelca para generar los tipos
del front (`make types`).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import __version__
from .routers import (
    analysis,
    boards,
    drills,
    engines,
    games,
    health,
    pgn_import,
    repertoire,
    replays,
    sparring,
    stats,
    sync,
    training,
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
app.include_router(training.router)
app.include_router(drills.router)
app.include_router(replays.router)
app.include_router(sparring.router)

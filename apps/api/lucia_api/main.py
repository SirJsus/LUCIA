from fastapi import FastAPI

from . import __version__
from .routers import health, sync

app = FastAPI(
    title="L.U.C.I.A. API",
    description="Logic & Ultimate Chess Insight Algorithm",
    version=__version__,
)

app.include_router(health.router)
app.include_router(sync.router)

# TODO Fase 1: routers games, analysis (+ WebSocket), stats, engines

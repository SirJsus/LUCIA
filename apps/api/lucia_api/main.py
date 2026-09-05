from fastapi import FastAPI

from . import __version__
from .routers import health

app = FastAPI(
    title="L.U.C.I.A. API",
    description="Logic & Ultimate Chess Insight Algorithm",
    version=__version__,
)

app.include_router(health.router)

# TODO Fase 1: routers sync, games, analysis (+ WebSocket), stats, engines

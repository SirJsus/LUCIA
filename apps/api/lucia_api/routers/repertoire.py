"""GET /repertoire y POST /repertoire/refresh — comparación del repertorio
propio con la teoría de maestros (RF-3.6).

Los dos endpoints están separados a propósito, y no es un detalle de
implementación: **`GET` no sale a internet nunca** y `POST /refresh` es lo
único de LUCIA que necesita red mientras se usa (ADR-0010). Quien mira el
repertorio sin conexión ve lo que ya se preguntó y cuánto falta; quien quiere
completarlo, pulsa.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from lucia_lichess import LichessExplorerAuthError, LichessExplorerClient, LichessExplorerError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import resolved_username
from lucia_api.services.repertoire import (
    DEFAULT_REFRESH_BUDGET,
    compare_repertoire,
    refresh_repertoire,
)
from lucia_api.settings import settings

router = APIRouter(tags=["repertoire"])

#: Tope por petición. Las posiciones se preguntan de una en una y espaciadas,
#: así que un tope alto dejaría la petición HTTP colgada minutos.
MAX_REFRESH_BUDGET = 60


class DepartureOut(BaseModel):
    """Un punto donde el repertorio propio se separa del de los maestros."""

    ply: int
    san: str
    """La jugada propia que ya no es teoría."""
    color: str
    master_moves: list[str]
    """Lo que juegan los maestros ahí, de más a menos frecuente."""
    games: int
    wins: int
    draws: int
    losses: int
    score_percent: float


class RepertoireOut(BaseModel):
    departures: list[DepartureOut]
    games_compared: int
    positions_known: int
    positions_missing: int
    """Posiciones que aún no se le han preguntado a Lichess. Mientras no sea
    cero, la comparación está incompleta."""
    explorer_token_configured: bool
    """Si hay token de Lichess configurado. Sin él no se puede consultar nada,
    así que la pantalla lo dice **antes** de que el usuario pulse, en vez de
    dejarle descubrirlo con un error (criterio C-3)."""
    positions_per_refresh: int
    """Cuántas posiciones trae como mucho una consulta, y cuánto se espera
    entre ellas: con esos dos números la pantalla puede decir qué va a pasar al
    pulsar, en vez de dejar al usuario delante de una barra sin final."""
    seconds_between_positions: float


class RefreshResultOut(BaseModel):
    fetched: int
    remaining: int


@router.get("/repertoire", response_model=RepertoireOut)
async def player_repertoire(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
) -> RepertoireOut:
    """Dónde se sale el jugador de la teoría, con lo que ya está en la caché."""
    comparison = await compare_repertoire(session, resolved_username(username))
    return RepertoireOut(
        departures=[
            DepartureOut(**vars(item), score_percent=item.score_percent)
            for item in comparison.departures
        ],
        games_compared=comparison.games_compared,
        positions_known=comparison.positions_known,
        positions_missing=comparison.positions_missing,
        explorer_token_configured=bool(settings.lichess_token),
        positions_per_refresh=DEFAULT_REFRESH_BUDGET,
        seconds_between_positions=settings.explorer_min_interval_seconds,
    )


@router.post("/repertoire/refresh", response_model=RefreshResultOut)
async def refresh_player_repertoire(
    session: Annotated[AsyncSession, Depends(get_session)],
    username: str | None = None,
    budget: Annotated[int, Query(ge=1, le=MAX_REFRESH_BUDGET)] = DEFAULT_REFRESH_BUDGET,
) -> RefreshResultOut:
    """Pregunta a Lichess por las posiciones que falten, hasta `budget`.

    Devuelve cuántas se preguntaron y cuántas siguen faltando, que es lo que
    permite a la pantalla decir si hace falta volver a pulsar.
    """
    user_agent = settings.lichess_user_agent or settings.chesscom_user_agent
    try:
        async with LichessExplorerClient(
            user_agent,
            token=settings.lichess_token,
            min_interval_seconds=settings.explorer_min_interval_seconds,
        ) as client:
            fetched, remaining = await refresh_repertoire(
                session, client, resolved_username(username), budget
            )
    except LichessExplorerAuthError as error:
        # Falta el token o no vale: tiene arreglo y quien lo sufre puede
        # aplicarlo, así que se distingue de "el servicio no responde".
        raise HTTPException(status_code=401, detail=str(error)) from error
    except LichessExplorerError as error:
        # El explorador es de otro: que falle no es un fallo de LUCIA, y lo que
        # se hubiera conseguido antes del fallo ya está guardado.
        raise HTTPException(
            status_code=502, detail=f"el explorador de Lichess no respondió: {error}"
        ) from error
    return RefreshResultOut(fetched=fetched, remaining=remaining)

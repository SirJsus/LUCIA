"""GET/PUT /engines/config — configuración de los motores (RF-5.4).

Editable: hilos, hash, profundidad y MultiPV. **No** editable: la ruta del
binario, que se expone solo en lectura — aceptarla por HTTP equivaldría a
ejecutar un ejecutable arbitrario del sistema desde el navegador.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.services.engines import (
    ENGINE_NAMES,
    EffectiveEngineConfig,
    get_effective_config,
    update_config,
)

router = APIRouter(tags=["engines"])


class EngineConfigOut(BaseModel):
    name: str
    threads: int
    hash_mb: int
    depth: int
    multipv: int
    path: str
    available: bool
    """Si el binario existe en esa ruta. No confirma que responda UCI."""
    weights_path: str | None = None
    weights_available: bool | None = None


class EnginesConfigOut(BaseModel):
    stockfish: EngineConfigOut
    lc0: EngineConfigOut


class EngineConfigUpdate(BaseModel):
    """Los rangos evitan configuraciones que colgarían la máquina (o el
    análisis) sin darse cuenta: un `depth` de 60 no termina nunca."""

    threads: int = Field(ge=1, le=64)
    hash_mb: int = Field(ge=16, le=8192)
    depth: int = Field(ge=1, le=40)
    multipv: int = Field(ge=1, le=10)


def _to_out(config: EffectiveEngineConfig) -> EngineConfigOut:
    return EngineConfigOut(
        name=config.name,
        threads=config.threads,
        hash_mb=config.hash_mb,
        depth=config.depth,
        multipv=config.multipv,
        path=str(config.path),
        available=config.path.exists(),
        weights_path=str(config.weights_path) if config.weights_path else None,
        weights_available=config.weights_path.exists() if config.weights_path else None,
    )


@router.get("/engines/config", response_model=EnginesConfigOut)
async def engines_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EnginesConfigOut:
    return EnginesConfigOut(
        stockfish=_to_out(await get_effective_config(session, "stockfish")),
        lc0=_to_out(await get_effective_config(session, "lc0")),
    )


@router.put("/engines/config/{engine_name}", response_model=EngineConfigOut)
async def update_engine_config(
    engine_name: str,
    body: EngineConfigUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EngineConfigOut:
    if engine_name not in ENGINE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"motor desconocido: {engine_name!r}. Conocidos: {list(ENGINE_NAMES)}",
        )
    config = await update_config(
        session,
        engine_name,
        threads=body.threads,
        hash_mb=body.hash_mb,
        depth=body.depth,
        multipv=body.multipv,
    )
    return _to_out(config)

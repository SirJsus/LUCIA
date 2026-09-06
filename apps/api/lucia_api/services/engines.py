"""Configuración efectiva de los motores (RF-5.4).

"Efectiva" = lo que hay en `engine_settings` si el usuario lo editó alguna
vez, o los valores por defecto de `.env` si no. Así la UI puede ajustar
profundidad, MultiPV, hilos y hash sin tocar archivos, y un clon nuevo del
repo sigue funcionando sin haber configurado nada.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import EngineSettings
from lucia_api.settings import settings

ENGINE_NAMES = ("stockfish", "lc0")


@dataclass(frozen=True)
class EffectiveEngineConfig:
    """Config lista para usar: parámetros editables + rutas de solo lectura."""

    name: str
    threads: int
    hash_mb: int
    depth: int
    multipv: int
    path: Path
    """De `.env`, nunca editable por HTTP (sería ejecución arbitraria)."""
    weights_path: Path | None = None
    """Solo Lc0: red neuronal a cargar."""


def default_config(name: str) -> EffectiveEngineConfig:
    """Valores por defecto cuando el motor no se ha configurado nunca."""
    if name not in ENGINE_NAMES:
        raise ValueError(f"motor desconocido: {name!r}")
    return EffectiveEngineConfig(
        name=name,
        threads=1,
        hash_mb=256,
        depth=settings.analysis_depth,
        multipv=settings.analysis_multipv,
        path=settings.stockfish_path if name == "stockfish" else settings.lc0_path,
        weights_path=None if name == "stockfish" else settings.lc0_weights,
    )


async def get_effective_config(session: AsyncSession, name: str) -> EffectiveEngineConfig:
    base = default_config(name)
    guardada = await session.get(EngineSettings, name)
    if guardada is None:
        return base
    return EffectiveEngineConfig(
        name=base.name,
        threads=guardada.threads,
        hash_mb=guardada.hash_mb,
        depth=guardada.depth,
        multipv=guardada.multipv,
        path=base.path,
        weights_path=base.weights_path,
    )


async def update_config(
    session: AsyncSession,
    name: str,
    *,
    threads: int,
    hash_mb: int,
    depth: int,
    multipv: int,
) -> EffectiveEngineConfig:
    """Crea o actualiza la fila de ese motor y devuelve la config resultante."""
    if name not in ENGINE_NAMES:
        raise ValueError(f"motor desconocido: {name!r}")

    fila = await session.get(EngineSettings, name)
    if fila is None:
        fila = EngineSettings(name=name)
        session.add(fila)
    fila.threads = threads
    fila.hash_mb = hash_mb
    fila.depth = depth
    fila.multipv = multipv
    fila.updated_at = dt.datetime.now(dt.UTC)
    await session.commit()

    return await get_effective_config(session, name)

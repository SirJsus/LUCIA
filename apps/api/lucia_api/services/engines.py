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
    backend: str | None = None
    """Solo Lc0: backend de cómputo (ver `Settings.lc0_backend`)."""

    @property
    def limit_kind(self) -> str:
        """Unidad en la que se le pide esfuerzo al motor.

        No se guarda en la base ni se puede configurar: se deriva del motor
        porque es una propiedad suya, no una preferencia. Stockfish busca en
        profundidad (alfa-beta) y "profundidad 18" significa algo concreto.
        Lc0 explora con MCTS, donde la profundidad es un promedio del árbol y
        pedir una concreta puede costar un número imprevisible de
        evaluaciones de red; ahí lo predecible es acotar los nodos.
        """
        return "nodes" if self.name == "lc0" else "depth"

    def uci_extra_options(self) -> dict[str, str | int | bool]:
        """Opciones UCI propias del motor, más allá de hilos y hash."""
        if self.weights_path is None:
            return {}
        uci_options: dict[str, str | int | bool] = {"WeightsFile": str(self.weights_path)}
        if self.backend:
            uci_options["Backend"] = self.backend
        return uci_options


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
        backend=None if name == "stockfish" else settings.lc0_backend,
    )


async def get_effective_config(session: AsyncSession, name: str) -> EffectiveEngineConfig:
    base = default_config(name)
    saved_settings = await session.get(EngineSettings, name)
    if saved_settings is None:
        return base
    return EffectiveEngineConfig(
        name=base.name,
        threads=saved_settings.threads,
        hash_mb=saved_settings.hash_mb,
        depth=saved_settings.depth,
        multipv=saved_settings.multipv,
        path=base.path,
        weights_path=base.weights_path,
        backend=base.backend,
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

    settings_row = await session.get(EngineSettings, name)
    if settings_row is None:
        settings_row = EngineSettings(name=name)
        session.add(settings_row)
    settings_row.threads = threads
    settings_row.hash_mb = hash_mb
    settings_row.depth = depth
    settings_row.multipv = multipv
    settings_row.updated_at = dt.datetime.now(dt.UTC)
    await session.commit()

    return await get_effective_config(session, name)

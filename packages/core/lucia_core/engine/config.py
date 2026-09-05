from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class EngineConfig(BaseModel):
    """Configuración de un motor UCI (Stockfish, Lc0 o cualquier otro)."""

    name: str = Field(description="Identificador legible, p.ej. 'stockfish' o 'lc0'")
    path: Path = Field(description="Ruta al binario del motor")
    threads: int = 1
    hash_mb: int = 256
    multipv: int = 3
    limit_kind: Literal["depth", "nodes", "time"] = "depth"
    limit_value: int = 18
    extra_options: dict[str, str | int | bool] = Field(
        default_factory=dict,
        description="Opciones UCI adicionales, p.ej. {'WeightsFile': '...'} para Lc0",
    )

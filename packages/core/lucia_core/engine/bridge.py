"""Puente asíncrono con un motor UCI usando python-chess.

TODO (Fase 1):
- open()/close() con chess.engine.popen_uci
- analyse(board) -> lista de PVs con eval en cp/mate
- pool de N instancias para análisis en lote
"""

from __future__ import annotations

import chess
import chess.engine

from .config import EngineConfig


class EngineBridge:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self._engine: chess.engine.Protocol | None = None

    async def open(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    async def analyse(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        raise NotImplementedError

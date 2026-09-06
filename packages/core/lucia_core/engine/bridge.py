"""Puente asíncrono con un motor UCI (Stockfish, Lc0 o cualquier otro),
usando `python-chess` para hablar el protocolo."""

from __future__ import annotations

import chess
import chess.engine

from .config import EngineConfig


class EngineBridge:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self._engine: chess.engine.UciProtocol | None = None

    async def open(self) -> None:
        _transport, engine = await chess.engine.popen_uci(str(self.config.path))
        self._engine = engine
        await self._engine.configure(self._opciones_a_aplicar())

    def _opciones_a_aplicar(self) -> dict[str, str | int | bool]:
        """Qué opciones UCI mandarle a este motor en concreto.

        `Threads` y `Hash` son "estándar" de facto, pero no universales: Lc0
        acepta `Threads` y no `Hash` (usa `NNCacheSize`, que además se mide en
        posiciones, no en MB, así que no es un equivalente). Mandar una opción
        que el motor no conoce aborta la conexión, así que las genéricas se
        aplican solo si el motor las declara — eso también hace que enchufar
        un motor UCI cualquiera funcione sin tocar código (RNF-9).

        `extra_options` es la excepción: se aplican siempre, sin filtrar,
        porque las pidió explícitamente quien configuró el motor. Si no
        existen, es un error de configuración y conviene que se note.
        """
        if self._engine is None:
            raise RuntimeError("el motor no está abierto")

        soportadas = self._engine.options
        genericas: dict[str, str | int | bool] = {
            "Threads": self.config.threads,
            "Hash": self.config.hash_mb,
        }
        opciones = {k: v for k, v in genericas.items() if k in soportadas}
        opciones.update(self.config.extra_options)
        return opciones

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.quit()
            self._engine = None

    async def __aenter__(self) -> EngineBridge:
        await self.open()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def analyse(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        """Analiza `board` y devuelve una línea por cada `multipv` configurado,
        ordenadas de mejor a peor (índice 0 = mejor jugada del motor)."""
        if self._engine is None:
            raise RuntimeError(
                "El motor no está abierto: usa 'async with EngineBridge(...)' "
                "o llama a open() antes."
            )
        return await self._engine.analyse(board, self._limit(), multipv=self.config.multipv)

    def _limit(self) -> chess.engine.Limit:
        kind, value = self.config.limit_kind, self.config.limit_value
        if kind == "depth":
            return chess.engine.Limit(depth=value)
        if kind == "nodes":
            return chess.engine.Limit(nodes=value)
        return chess.engine.Limit(time=value)

"""Puente asíncrono con un motor UCI (Stockfish, Lc0 o cualquier otro),
usando `python-chess` para hablar el protocolo.

Dos formas de usarlo, y no son la misma pregunta: `analyze()` pide la opinión
del motor sobre una posición —de ahí vive todo RF-2, a través de
`lucia_core.analysis` y del `CachedEngineBridge` de la API— y `play()` le pide
que **mueva**, que es lo que hace posible jugar contra él (RF-4.3, desde
`lucia_api.services.sparring`).

Aquí solo se habla UCI: qué motor hay al otro lado, con qué red y con cuánta
fuerza lo decide quien arma el `EngineConfig`, fuera del núcleo (RNF-9).
"""

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
        await self._engine.configure(self._options_to_apply())

    def _options_to_apply(self) -> dict[str, str | int | bool]:
        """Qué opciones UCI mandarle a este motor en concreto.

        `Threads` y `Hash` son "estándar" de facto, pero no universales: Lc0
        acepta `Threads` y no `Hash` (usa `NNCacheSize`, que además se mide en
        posiciones, no en MB, así que no es un equivalente). Mandar una opción
        que el motor no conoce aborta la conexión, así que las genéricas se
        aplican solo si el motor las declara — eso también hace que enchufar
        un motor UCI cualquiera funcione sin tocar código (RNF-9).

        `UCI_ShowWDL` va por la misma vía y por la misma razón. Es lo que hace
        que el motor informe de su probabilidad de victoria, tablas y derrota
        (RF-2.6) en vez de solo del centipeón; lo declaran tanto Stockfish como
        Lc0, pero no tiene por qué declararlo un motor cualquiera, y pedírselo
        a quien no lo conoce abortaría la conexión. Sin él, `python-chess` no
        recibe `wdl` en las líneas y `EngineLine.wdl` se queda en `None`, que
        es justo lo que debe pasar con un motor que no sabe contestarlo.

        `extra_options` es la excepción: se aplican siempre, sin filtrar,
        porque las pidió explícitamente quien configuró el motor. Si no
        existen, es un error de configuración y conviene que se note.
        """
        if self._engine is None:
            raise RuntimeError("el motor no está abierto")

        supported_options = self._engine.options
        generic_options: dict[str, str | int | bool] = {
            "Threads": self.config.threads,
            "Hash": self.config.hash_mb,
            "UCI_ShowWDL": True,
        }
        options = {k: v for k, v in generic_options.items() if k in supported_options}
        options.update(self.config.extra_options)
        return options

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.quit()
            self._engine = None

    async def __aenter__(self) -> EngineBridge:
        await self.open()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def analyze(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        """Analiza `board` y devuelve una línea por cada `multipv` configurado,
        ordenadas de mejor a peor (índice 0 = mejor jugada del motor)."""
        engine = self._require_open_engine()
        return await engine.analyse(board, self._limit(), multipv=self.config.multipv)

    async def play(self, board: chess.Board) -> chess.Move:
        """La jugada que el motor **haría** en `board`, no la que recomienda.

        Es la otra forma de hablar con un motor UCI, y la que hacía falta para
        jugar contra él (RF-4.3): `analyze` pregunta "qué es lo mejor aquí" y
        siempre contesta lo mismo, mientras que `play` le pide que mueva, y
        entonces respeta lo que se le haya pedido de fuerza —`UCI_LimitStrength`
        y `UCI_Elo` en Stockfish, la red Maia y un solo nodo en Lc0— que es
        justo lo que hace de rival calibrado y no de oráculo.

        Quién decide esa fuerza está fuera del núcleo, en `EngineConfig`
        (`extra_options` y el límite de búsqueda): aquí solo se habla UCI, sin
        saber qué motor hay al otro lado (RNF-9).

        No se le pregunta por una posición ya terminada: en jaque mate o
        ahogado no hay jugada que devolver y Lc0 se queda esperando para
        siempre, que es el mismo cuidado que tiene `evaluate_positions`.
        """
        if board.is_game_over(claim_draw=True):
            raise ValueError("la partida ya terminó: no hay jugada que pedirle al motor")
        engine = self._require_open_engine()
        played = await engine.play(board, self._limit())
        if played.move is None:
            raise RuntimeError(f"{self.config.name} no devolvió jugada en {board.fen()}")
        return played.move

    def _require_open_engine(self) -> chess.engine.UciProtocol:
        if self._engine is None:
            raise RuntimeError(
                "El motor no está abierto: usa 'async with EngineBridge(...)' "
                "o llama a open() antes."
            )
        return self._engine

    def _limit(self) -> chess.engine.Limit:
        kind, value = self.config.limit_kind, self.config.limit_value
        if kind == "depth":
            return chess.engine.Limit(depth=value)
        if kind == "nodes":
            return chess.engine.Limit(nodes=value)
        return chess.engine.Limit(time=value)

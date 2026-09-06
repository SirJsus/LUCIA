"""Servicio de análisis (RF-2): orquesta `lucia_core` y persiste en SQLite,
con caché de posiciones por FEN (RF-2.7)."""

from __future__ import annotations

import datetime as dt
import io
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import chess
import chess.engine
import chess.pgn
from lucia_core.analysis import analyze_game
from lucia_core.engine import EngineBridge, EngineConfig
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove, Game, PositionCache
from lucia_api.services.engines import get_effective_config

ProgressCallback = Callable[[int, int], Awaitable[None]]


class CachedEngineBridge:
    """Envuelve un `EngineBridge` real y cachea por FEN en `position_cache`.

    Solo cachea cuando el límite del motor es por profundidad: con límite de
    tiempo o de nodos, dos búsquedas "iguales sobre el papel" pueden explorar
    cantidades distintas de posiciones (según qué tan cargada esté la
    máquina), así que no son intercambiables y no vale la pena cachearlas.
    Satisface el mismo `Protocol` que `lucia_core.analysis.AnalysingEngine`
    (solo necesita `analyse(board)`), sin que `lucia_core` sepa de bases de
    datos.
    """

    def __init__(self, session: AsyncSession, engine: EngineBridge, engine_name: str) -> None:
        self._session = session
        self._engine = engine
        self._engine_name = engine_name

    async def analyse(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        config = self._engine.config
        if config.limit_kind != "depth":
            return await self._engine.analyse(board)

        clave = {
            "fen": board.fen(),
            "engine": self._engine_name,
            "depth": config.limit_value,
            "multipv": config.multipv,
        }
        en_cache = await self._session.get(PositionCache, clave)
        if en_cache is not None:
            return [_deserializar_linea(linea) for linea in en_cache.lines_json]

        lineas = await self._engine.analyse(board)
        self._session.add(
            PositionCache(**clave, lines_json=[_serializar_linea(linea) for linea in lineas])
        )
        await self._session.flush()
        return lineas


def _serializar_linea(linea: chess.engine.InfoDict) -> dict:
    score = linea["score"].white()
    return {
        "score_cp": None if score.is_mate() else score.score(),
        "score_mate": score.mate() if score.is_mate() else None,
        "pv": [m.uci() for m in (linea.get("pv") or [])],
    }


def _deserializar_linea(data: dict) -> chess.engine.InfoDict:
    puntaje = (
        chess.engine.Mate(data["score_mate"])
        if data["score_mate"] is not None
        else chess.engine.Cp(data["score_cp"])
    )
    return {
        "score": chess.engine.PovScore(puntaje, chess.WHITE),
        "pv": [chess.Move.from_uci(u) for u in data["pv"]],
    }


@dataclass(frozen=True)
class EngineLine:
    """Una línea del motor para una posición suelta (RF-5.2 / RF-6.2)."""

    rank: int
    score_cp: int | None
    score_mate: int | None
    """Positivo = mate a favor de las blancas (todo se guarda desde su punto de vista)."""
    pv_uci: list[str]
    pv_san: list[str]


async def analyse_position(
    session: AsyncSession,
    fen: str,
    *,
    engine_name: str = "stockfish",
    depth: int | None = None,
    multipv: int | None = None,
) -> list[EngineLine]:
    """Analiza una posición y devuelve sus mejores líneas, ordenadas.

    Es síncrono a propósito: a diferencia del análisis de una partida entera
    (que se encola), aquí se espera una respuesta inmediata para el tablero de
    análisis. Por eso conviene una profundidad moderada, y por eso el router
    la acota.
    """
    board = chess.Board(fen)  # lanza ValueError si el FEN es inválido
    config_motor = await get_effective_config(session, engine_name)
    config = EngineConfig(
        name=engine_name,
        path=config_motor.path,
        threads=config_motor.threads,
        hash_mb=config_motor.hash_mb,
        multipv=multipv or config_motor.multipv,
        limit_kind="depth",
        limit_value=depth or config_motor.depth,
        extra_options=(
            {"WeightsFile": str(config_motor.weights_path)} if config_motor.weights_path else {}
        ),
    )

    async with EngineBridge(config) as motor_real:
        # Se reutiliza la misma caché que el análisis de partidas: explorar
        # variantes suele volver a posiciones ya vistas.
        motor = CachedEngineBridge(session, motor_real, engine_name)
        lineas = await motor.analyse(board)
    await session.commit()

    resultado: list[EngineLine] = []
    for rank, linea in enumerate(lineas, start=1):
        score = linea["score"].white()
        pv = list(linea.get("pv") or [])
        resultado.append(
            EngineLine(
                rank=rank,
                score_cp=None if score.is_mate() else score.score(),
                score_mate=score.mate() if score.is_mate() else None,
                pv_uci=[m.uci() for m in pv],
                pv_san=_pv_to_san(board, pv),
            )
        )
    return resultado


def _pv_to_san(board: chess.Board, pv: list[chess.Move]) -> list[str]:
    """La notación SAN depende de la posición, así que hay que ir aplicando
    las jugadas para nombrarlas bien (`Nf3` puede ser `Ngf3` según el caso)."""
    tablero = board.copy()
    san: list[str] = []
    for move in pv:
        if move not in tablero.legal_moves:
            break  # una PV de la caché puede no encajar si el FEN no coincide
        san.append(tablero.san(move))
        tablero.push(move)
    return san


async def run_analysis(
    session: AsyncSession,
    analysis: Analysis,
    game: Game,
    on_progress: ProgressCallback | None = None,
) -> None:
    """Ejecuta el análisis de `game` y persiste el resultado en `analysis`.

    Dejar `analysis` en estado "error" en vez de propagar la excepción es a
    propósito: quien llama (el worker) es un job en background sin nadie
    esperando el resultado en la misma corrutina; la única forma de que el
    error no se pierda en silencio es guardarlo en la fila.
    """
    try:
        partida = chess.pgn.read_game(io.StringIO(game.pgn))
        if partida is None:
            raise ValueError(f"PGN inválido en la partida {game.id}")
        jugadas = list(partida.mainline_moves())

        # `depth` y `multipv` salen de la fila `Analysis` (quedaron fijados al
        # encolar, para que el resultado sea reproducible aunque después se
        # cambie la config); `threads` y `hash_mb`, de la config vigente.
        config_motor = await get_effective_config(session, analysis.engine)
        config = EngineConfig(
            name=analysis.engine,
            path=config_motor.path,
            threads=config_motor.threads,
            hash_mb=config_motor.hash_mb,
            multipv=analysis.multipv,
            limit_kind="depth",
            limit_value=analysis.depth,
            # Lc0 no arranca sin su red neuronal; Stockfish no usa esta opción.
            extra_options=(
                {"WeightsFile": str(config_motor.weights_path)} if config_motor.weights_path else {}
            ),
        )

        analysis.status = "running"
        await session.commit()

        async with EngineBridge(config) as motor_real:
            motor = CachedEngineBridge(session, motor_real, analysis.engine)
            resultado = await analyze_game(motor, chess.Board(), jugadas, on_position=on_progress)

        for jugada in resultado.moves:
            session.add(
                AnalyzedMove(
                    analysis_id=analysis.id,
                    ply=jugada.ply,
                    color="white" if jugada.color == chess.WHITE else "black",
                    san=jugada.san,
                    uci=jugada.uci,
                    fen_before=jugada.fen_before,
                    classification=jugada.classification,
                    phase=jugada.phase,
                    move_accuracy=jugada.accuracy,
                    win_percent_before=jugada.win_percent_before,
                    win_percent_after=jugada.win_percent_after,
                    best_move_uci=jugada.best_move_uci,
                )
            )
        analysis.white_accuracy = resultado.white_accuracy
        analysis.black_accuracy = resultado.black_accuracy
        analysis.status = "done"
    except Exception as error:  # noqa: BLE001 — se guarda el motivo, no se traga
        analysis.status = "error"
        analysis.error = str(error)
    finally:
        analysis.finished_at = dt.datetime.now(dt.UTC)
        await session.commit()

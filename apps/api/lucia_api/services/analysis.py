"""Servicio de análisis (RF-2): orquesta `lucia_core` y persiste en SQLite,
con caché de posiciones por FEN (RF-2.7)."""

from __future__ import annotations

import datetime as dt
import io
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

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

    No cachea con límite de **tiempo**: dos búsquedas de "un segundo" exploran
    cantidades distintas según lo cargada que esté la máquina, así que no son
    intercambiables. Con profundidad o con nodos sí, porque ambos son
    deterministas — y eso importa especialmente con Lc0, que va por nodos y es
    lento: sin caché volvería a evaluar cada posición de apertura repetida.

    En la clave, el valor del límite se guarda en la columna `depth`; la
    unidad se deduce del motor (ver `EffectiveEngineConfig.limit_kind`), y
    como el motor forma parte de la clave, no hay ambigüedad posible. Para
    Lc0, ese "motor" incluye el nombre de la red (`lc0/744706-conv.pb.gz`),
    porque cambiar de red cambia por completo la evaluación.

    Satisface el mismo `Protocol` que `lucia_core.analysis.AnalyzingEngine`
    (solo necesita `analyze(board)`), sin que `lucia_core` sepa de bases de
    datos.
    """

    def __init__(self, session: AsyncSession, engine: EngineBridge, engine_name: str) -> None:
        self._session = session
        self._engine = engine
        # La clave de caché incluye la red neuronal, no solo el nombre del
        # motor: el mismo Lc0 con otra red da evaluaciones distintas para la
        # misma posición, y sin esto devolvería las de la red anterior.
        weights_file = engine.config.extra_options.get("WeightsFile")
        self._engine_name = (
            f"{engine_name}/{Path(str(weights_file)).name}" if weights_file else engine_name
        )

    async def analyze(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        config = self._engine.config
        if config.limit_kind == "time":
            return await self._engine.analyze(board)

        cache_key = {
            "fen": board.fen(),
            "engine": self._engine_name,
            "depth": config.limit_value,
            "multipv": config.multipv,
        }
        cached_position = await self._session.get(PositionCache, cache_key)
        if cached_position is not None:
            return [
                _deserialize_line(serialized_line) for serialized_line in cached_position.lines_json
            ]

        lines = await self._engine.analyze(board)
        self._session.add(
            PositionCache(**cache_key, lines_json=[_serialize_line(line) for line in lines])
        )
        await self._session.flush()
        return lines


def _serialize_line(line: chess.engine.InfoDict) -> dict:
    score = line["score"].white()
    return {
        "score_cp": None if score.is_mate() else score.score(),
        "score_mate": score.mate() if score.is_mate() else None,
        "pv": [m.uci() for m in (line.get("pv") or [])],
    }


def _deserialize_line(serialized_line: dict) -> chess.engine.InfoDict:
    score = (
        chess.engine.Mate(serialized_line["score_mate"])
        if serialized_line["score_mate"] is not None
        else chess.engine.Cp(serialized_line["score_cp"])
    )
    return {
        "score": chess.engine.PovScore(score, chess.WHITE),
        "pv": [chess.Move.from_uci(move_uci) for move_uci in serialized_line["pv"]],
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


async def analyze_position(
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
    effective_config = await get_effective_config(session, engine_name)
    config = EngineConfig(
        name=engine_name,
        path=effective_config.path,
        threads=effective_config.threads,
        hash_mb=effective_config.hash_mb,
        multipv=multipv or effective_config.multipv,
        limit_kind=effective_config.limit_kind,
        limit_value=depth or effective_config.depth,
        extra_options=effective_config.uci_extra_options(),
    )

    async with EngineBridge(config) as real_engine:
        # Se reutiliza la misma caché que el análisis de partidas: explorar
        # variantes suele volver a posiciones ya vistas.
        cached_engine = CachedEngineBridge(session, real_engine, engine_name)
        raw_lines = await cached_engine.analyze(board)
    await session.commit()

    lines: list[EngineLine] = []
    for rank, raw_line in enumerate(raw_lines, start=1):
        score = raw_line["score"].white()
        pv = list(raw_line.get("pv") or [])
        lines.append(
            EngineLine(
                rank=rank,
                score_cp=None if score.is_mate() else score.score(),
                score_mate=score.mate() if score.is_mate() else None,
                pv_uci=[m.uci() for m in pv],
                pv_san=_pv_to_san(board, pv),
            )
        )
    return lines


def _pv_to_san(board: chess.Board, pv: list[chess.Move]) -> list[str]:
    """La notación SAN depende de la posición, así que hay que ir aplicando
    las jugadas para nombrarlas bien (`Nf3` puede ser `Ngf3` según el caso)."""
    replay_board = board.copy()
    san: list[str] = []
    for move in pv:
        if move not in replay_board.legal_moves:
            break  # una PV de la caché puede no encajar si el FEN no coincide
        san.append(replay_board.san(move))
        replay_board.push(move)
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
        pgn_game = chess.pgn.read_game(io.StringIO(game.pgn))
        if pgn_game is None:
            raise ValueError(f"PGN inválido en la partida {game.id}")
        # La posición inicial sale del PGN, no de `chess.Board()`: chess.com
        # marca con `[SetUp "1"]` + `[FEN ...]` las partidas que no empiezan en
        # la posición estándar (odds chess, Chess960, "partidas desde
        # posición"), y replicarlas sobre el tablero de siempre daba jugadas
        # ilegales. `pgn_game.board()` además marca `chess960` cuando toca, y
        # con eso `python-chess` negocia solo el `UCI_Chess960` con el motor.
        pgn_starting_board = pgn_game.board()
        moves = list(pgn_game.mainline_moves())

        # `depth` y `multipv` salen de la fila `Analysis` (quedaron fijados al
        # encolar, para que el resultado sea reproducible aunque después se
        # cambie la config); `threads` y `hash_mb`, de la config vigente.
        effective_config = await get_effective_config(session, analysis.engine)
        config = EngineConfig(
            name=analysis.engine,
            path=effective_config.path,
            threads=effective_config.threads,
            hash_mb=effective_config.hash_mb,
            multipv=analysis.multipv,
            limit_kind=effective_config.limit_kind,
            limit_value=analysis.depth,
            # Lc0 necesita su red y su backend; Stockfish no usa ninguna.
            extra_options=effective_config.uci_extra_options(),
        )

        analysis.status = "running"
        await session.commit()

        async with EngineBridge(config) as real_engine:
            cached_engine = CachedEngineBridge(session, real_engine, analysis.engine)
            analysis_result = await analyze_game(
                cached_engine, pgn_starting_board, moves, on_position=on_progress
            )

        for analyzed_move in analysis_result.moves:
            session.add(
                AnalyzedMove(
                    analysis_id=analysis.id,
                    ply=analyzed_move.ply,
                    color="white" if analyzed_move.color == chess.WHITE else "black",
                    san=analyzed_move.san,
                    uci=analyzed_move.uci,
                    fen_before=analyzed_move.fen_before,
                    classification=analyzed_move.classification,
                    phase=analyzed_move.phase,
                    move_accuracy=analyzed_move.accuracy,
                    win_percent_before=analyzed_move.win_percent_before,
                    win_percent_after=analyzed_move.win_percent_after,
                    best_move_uci=analyzed_move.best_move_uci,
                )
            )
        analysis.white_accuracy = analysis_result.white_accuracy
        analysis.black_accuracy = analysis_result.black_accuracy
        analysis.status = "done"
    except Exception as error:  # noqa: BLE001 — se guarda el motivo, no se traga
        analysis.status = "error"
        analysis.error = str(error)
    finally:
        analysis.finished_at = dt.datetime.now(dt.UTC)
        await session.commit()

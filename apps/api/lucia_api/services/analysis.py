"""Servicio de análisis (RF-2): orquesta `lucia_core` y persiste en SQLite,
con caché de posiciones por FEN (RF-2.7)."""

from __future__ import annotations

import datetime as dt
import io
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine
import chess.pgn
from lucia_core.analysis import analyze_game
from lucia_core.engine import EngineBridge, EngineConfig
from sqlalchemy import select
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
        self._engine_name = _cache_engine_name(engine_name, engine.config.extra_options)

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
            PositionCache(
                **cache_key,
                lines_json=[_serialize_line(line["score"], line.get("pv") or []) for line in lines],
            )
        )
        await self._session.flush()
        return lines


def _cache_engine_name(engine_name: str, extra_options: Mapping[str, object]) -> str:
    """El motor tal como aparece en la clave de `position_cache`.

    Para Lc0 incluye el nombre de la red (`lc0/744706-conv.pb.gz`): el mismo
    motor con otra red da evaluaciones distintas para la misma posición, y sin
    esto la caché devolvería las de la red anterior.
    """
    weights_file = extra_options.get("WeightsFile")
    return f"{engine_name}/{Path(str(weights_file)).name}" if weights_file else engine_name


def _serialize_line(score: chess.engine.PovScore, pv: Sequence[chess.Move]) -> dict:
    """Una línea del motor tal como se guarda en la base.

    Mismo formato en `position_cache.lines_json` y en
    `analyzed_moves.alternatives_json`: así una lista de líneas cacheada sirve
    tal cual como alternativas de una jugada, sin traducción de por medio
    (ADR-0007) — romper esa simetría rompe `alternatives_from_cache`. La
    puntuación va siempre desde el punto de vista de las blancas, como todo lo
    que se persiste.
    """
    white_score = score.white()
    return {
        "score_cp": None if white_score.is_mate() else white_score.score(),
        "score_mate": white_score.mate() if white_score.is_mate() else None,
        "pv": [move.uci() for move in pv],
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


async def alternatives_from_cache(
    session: AsyncSession, analysis: Analysis, moves: Sequence[AnalyzedMove]
) -> dict[int, list[dict]]:
    """Alternativas recuperadas de `position_cache`, por ply, para las jugadas
    que no las guardaron.

    Sirve para los análisis hechos **antes** de RF-10.1, que guardaron solo
    `best_move_uci`: sus posiciones sí quedaron en la caché con todas sus
    líneas (RF-2.7), así que las alternativas se pueden devolver sin volver a
    gastar motor, que es justamente por lo que RF-10 entró en el alcance de
    v1.0.

    Solo devuelve lo que encaja **exactamente** con la clave de la caché
    —misma posición, mismo motor y red, mismo límite y mismo MultiPV—, porque
    una línea calculada con otra configuración no es la que produjo esta
    clasificación. Lo que no encaje, no sale: mejor una flecha sola que una
    alternativa que el análisis nunca vio.

    No escribe nada: es una lectura de conveniencia en el camino de servir un
    análisis viejo, no una migración a medias.
    """
    fens_by_ply = {move.ply: move.fen_before for move in moves if move.alternatives_json is None}
    if not fens_by_ply:
        return {}

    effective_config = await get_effective_config(session, analysis.engine)
    engine_name = _cache_engine_name(analysis.engine, effective_config.uci_extra_options())
    cached_positions = await session.execute(
        select(PositionCache.fen, PositionCache.lines_json).where(
            PositionCache.fen.in_(set(fens_by_ply.values())),
            PositionCache.engine == engine_name,
            PositionCache.depth == analysis.depth,
            PositionCache.multipv == analysis.multipv,
        )
    )
    lines_by_fen = dict(cached_positions.all())
    return {ply: lines_by_fen[fen] for ply, fen in fens_by_ply.items() if fen in lines_by_fen}


def alternatives_of(move: AnalyzedMove, cached_alternatives: dict[int, list[dict]]) -> list[dict]:
    """Las alternativas de una jugada: las suyas, o las que `alternatives_from_cache`
    haya rescatado si el análisis es anterior a RF-10.1 y no las guardó."""
    if move.alternatives_json is not None:
        return move.alternatives_json
    return cached_alternatives.get(move.ply, [])


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

    En una posición terminal devuelve la lista vacía **sin abrir el motor**,
    por la misma razón que `lucia_core.analysis.evaluate_positions` no le
    pregunta ahí: no hay jugada que buscar, y preguntar rompe. Lc0 contesta
    `bestmove a1a1` —que no es UCI válido, así que `python-chess` aborta la
    conexión— o directamente se queda colgado. Se veía al llegar al final de
    una partida terminada en jaque mate en el tablero de análisis.
    """
    board = chess.Board(fen)  # lanza ValueError si el FEN es inválido
    if board.is_game_over():
        return []

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

    return _engine_lines(raw_lines, fen)


def engine_lines_from_serialized(serialized_lines: Sequence[dict], fen: str) -> list[EngineLine]:
    """Convierte líneas guardadas (`alternatives_json`, `lines_json`) en las
    mismas `EngineLine` que devuelve el análisis en vivo (RF-10.1)."""
    return _engine_lines([_deserialize_line(line) for line in serialized_lines], fen)


def _engine_lines(raw_lines: Sequence[chess.engine.InfoDict], fen: str) -> list[EngineLine]:
    """Numera las líneas del motor y las nombra desde `fen`: la notación SAN
    depende de la posición, así que no se guarda, se deriva al servir."""
    board = chess.Board(fen)
    lines: list[EngineLine] = []
    for rank, raw_line in enumerate(raw_lines, start=1):
        score = raw_line["score"].white()
        pv = list(raw_line.get("pv") or [])
        lines.append(
            EngineLine(
                rank=rank,
                score_cp=None if score.is_mate() else score.score(),
                score_mate=score.mate() if score.is_mate() else None,
                pv_uci=[move.uci() for move in pv],
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
                cached_engine,
                pgn_starting_board,
                moves,
                on_position=on_progress,
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
                    # RF-10.1: las N mejores líneas de la posición previa, no
                    # solo la mejor. Con MultiPV 1 la lista tiene un elemento.
                    alternatives_json=[
                        _serialize_line(line.score, line.pv) for line in analyzed_move.alternatives
                    ],
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

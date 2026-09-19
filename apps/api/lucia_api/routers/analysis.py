"""POST /analysis, GET /analysis/{id}, GET /analysis/{id}/pgn,
WS /ws/analysis/{id} — analizar partidas con motor (RF-2) usando
`lucia-core` como librería, y exportar el análisis a PGN anotado (RF-5.5)."""

from __future__ import annotations

import re
import unicodedata
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.dependencies import get_worker
from lucia_api.services.analysis import (
    alternatives_from_cache,
    alternatives_of,
    analyze_position,
    engine_lines_from_serialized,
)
from lucia_api.services.comparison import (
    DEFAULT_DISAGREEMENT_THRESHOLD,
    ComparisonError,
    compare_analyses,
)
from lucia_api.services.engines import get_effective_config
from lucia_api.services.insights import analysis_critical_moments
from lucia_api.services.pgn_export import export_annotated_pgn
from lucia_api.worker import AnalysisWorker

router = APIRouter(tags=["analysis"])

#: Tope de profundidad para el análisis en vivo de una posición. El endpoint
#: responde de forma síncrona, así que una búsqueda muy profunda bloquearía la
#: petición (y competiría con el worker por la CPU).
MAX_LIVE_DEPTH = 22


class AnalysisRequest(BaseModel):
    game_ids: list[int]
    engine: Literal["stockfish", "lc0"] = "stockfish"
    depth: int | None = None
    """Si se omite, usa `ANALYSIS_DEPTH` de la configuración."""
    multipv: int | None = None
    """Si se omite, usa `ANALYSIS_MULTIPV` de la configuración."""


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int | None
    """Nulo en un análisis de tablero (RF-6.9), donde lo que se llena es
    `board_id`. Los dos van llenos cuando el tablero está publicado como
    partida propia (RF-6.5, ADR-0014): las jugadas son del tablero y cuentan
    como las de esa partida."""
    board_id: int | None
    engine: str
    depth: int
    multipv: int
    status: str
    error: str | None
    white_accuracy: float | None
    black_accuracy: float | None


class EngineLineOut(BaseModel):
    """Una línea del motor, igual la calcule en vivo `POST /analysis/position`
    o venga guardada con una jugada analizada (RF-10.1): mismo formato en los
    dos sitios, para que el front la dibuje igual."""

    model_config = ConfigDict(from_attributes=True)

    rank: int
    score_cp: int | None
    score_mate: int | None
    pv_uci: list[str]
    pv_san: list[str]


class AnalyzedMoveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ply: int
    color: str
    san: str
    uci: str
    fen_before: str
    classification: str
    phase: str
    move_accuracy: float
    win_percent_before: float
    win_percent_after: float
    best_move_uci: str | None
    alternatives: list[EngineLineOut] = []
    """Lo que el motor proponía en la posición anterior a esta jugada, de mejor
    a peor (RF-10.1). Vacío en los análisis anteriores a RF-10 cuyas posiciones
    ya no están en la caché."""


class CriticalMomentOut(BaseModel):
    """Una posición donde la partida se decidía (RF-2.8)."""

    ply: int
    color: str
    """"white" | "black": de quién es la jugada. La probabilidad de victoria de
    abajo va desde su punto de vista, como en `AnalyzedMoveOut`; el front la
    gira a la de las blancas para enseñarla igual que la barra y el gráfico."""
    san: str
    kinds: list[str]
    """"only_move" (solo valía una jugada), "swing" (la partida cambió de manos)
    o "missed_chance" (había una ganada y se escapó); puede ser por más de un
    motivo a la vez."""
    win_percent_before: float
    win_percent_after: float
    best_alternative_san: str | None


class AnalysisDetail(AnalysisSummary):
    moves: list[AnalyzedMoveOut]
    critical_moments: list[CriticalMomentOut] = []
    """Las jugadas que decidieron la partida (RF-2.8). Se deducen de lo que ya
    está guardado —evaluaciones y alternativas—, sin volver a preguntar al
    motor; un análisis anterior a RF-10 sin alternativas recuperables sale con
    menos momentos, porque los de "jugada única" necesitan el MultiPV."""


@router.post("/analysis", response_model=list[AnalysisSummary])
async def create_analysis(
    body: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    worker: Annotated[AnalysisWorker, Depends(get_worker)],
) -> list[AnalysisSummary]:
    if not body.game_ids:
        raise HTTPException(status_code=422, detail="game_ids no puede estar vacío")

    # Sin `depth`/`multipv` explícitos se usa lo que el usuario dejó
    # configurado en /engines/config (RF-5.4), no el `.env` directamente.
    effective_config = await get_effective_config(session, body.engine)

    created_analyses: list[Analysis] = []
    for game_id in body.game_ids:
        game = await session.get(Game, game_id)
        if game is None:
            raise HTTPException(status_code=404, detail=f"no existe la partida {game_id}")
        analysis = Analysis(
            game_id=game_id,
            engine=body.engine,
            depth=body.depth or effective_config.depth,
            multipv=body.multipv or effective_config.multipv,
        )
        session.add(analysis)
        created_analyses.append(analysis)
    await session.commit()

    for analysis in created_analyses:
        await worker.enqueue(analysis.id)

    return [AnalysisSummary.model_validate(analysis) for analysis in created_analyses]


class PositionAnalysisRequest(BaseModel):
    fen: str
    engine: Literal["stockfish", "lc0"] = "stockfish"
    depth: int | None = Field(default=None, ge=1, le=MAX_LIVE_DEPTH)
    """Acotado: este endpoint responde de forma síncrona, y una profundidad
    alta dejaría la petición colgada minutos."""
    multipv: int | None = Field(default=None, ge=1, le=10)


@router.post("/analysis/position", response_model=list[EngineLineOut])
async def position_analysis(
    body: PositionAnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EngineLineOut]:
    """Analiza una posición suelta y devuelve las mejores líneas (RF-5.2 /
    RF-6.2). Para el tablero de análisis y la exploración en vivo."""
    try:
        lines = await analyze_position(
            session, body.fen, engine_name=body.engine, depth=body.depth, multipv=body.multipv
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"FEN inválido: {error}") from error
    return [EngineLineOut.model_validate(line) for line in lines]


@router.get("/analysis", response_model=list[AnalysisSummary])
async def list_analyses(
    session: Annotated[AsyncSession, Depends(get_session)],
    game_id: int | None = None,
    board_id: int | None = None,
) -> list[AnalysisSummary]:
    """Análisis existentes, opcionalmente los de una partida o un tablero
    concretos. Sirve para que el visor —y el tablero de análisis (RF-6.9)—
    sepan si ya hay uno hecho en vez de volver a analizar."""
    query = select(Analysis).order_by(Analysis.created_at.desc())
    if game_id is not None:
        query = query.where(Analysis.game_id == game_id)
    if board_id is not None:
        query = query.where(Analysis.board_id == board_id)
    result = await session.execute(query)
    return [AnalysisSummary.model_validate(analysis) for analysis in result.scalars().all()]


class MoveComparisonOut(BaseModel):
    ply: int
    color: str
    san: str
    classification_a: str
    classification_b: str
    win_percent_after_a: float
    win_percent_after_b: float
    win_percent_gap: float
    best_move_a: str | None
    best_move_b: str | None
    same_best_move: bool


class AnalysisComparisonOut(BaseModel):
    game_id: int
    analysis_a: int
    analysis_b: int
    engine_a: str
    engine_b: str
    total_moves: int
    agreed_best_moves: int
    best_move_agreement_percent: float
    disagreements: list[MoveComparisonOut]


@router.get("/analysis/compare", response_model=AnalysisComparisonOut)
async def compare(
    session: Annotated[AsyncSession, Depends(get_session)],
    analysis_a: int,
    analysis_b: int,
    threshold: Annotated[float, Query(ge=0, le=100)] = DEFAULT_DISAGREEMENT_THRESHOLD,
) -> AnalysisComparisonOut:
    """Dónde discrepan dos análisis de la misma partida (RF-2.6), típicamente
    uno de Stockfish y otro de Lc0."""
    try:
        comparison = await compare_analyses(session, analysis_a, analysis_b, threshold)
    except ComparisonError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return AnalysisComparisonOut(
        game_id=comparison.game_id,
        analysis_a=comparison.analysis_a,
        analysis_b=comparison.analysis_b,
        engine_a=comparison.engine_a,
        engine_b=comparison.engine_b,
        total_moves=comparison.total_moves,
        agreed_best_moves=comparison.agreed_best_moves,
        best_move_agreement_percent=comparison.best_move_agreement_percent,
        disagreements=[
            MoveComparisonOut(
                ply=disagreement.ply,
                color=disagreement.color,
                san=disagreement.san,
                classification_a=disagreement.classification_a,
                classification_b=disagreement.classification_b,
                win_percent_after_a=disagreement.win_percent_after_a,
                win_percent_after_b=disagreement.win_percent_after_b,
                win_percent_gap=disagreement.win_percent_gap,
                best_move_a=disagreement.best_move_a,
                best_move_b=disagreement.best_move_b,
                same_best_move=disagreement.same_best_move,
            )
            for disagreement in comparison.disagreements
        ],
    )


async def _load_analysis_with_moves(
    session: AsyncSession, analysis_id: int
) -> tuple[Analysis, list[AnalyzedMove], dict[int, list[dict]]]:
    """El análisis, sus jugadas en orden y las alternativas que haya que
    rescatar de la caché, que es lo que necesitan tanto el detalle como la
    exportación a PGN.

    Los análisis anteriores a RF-10.1 no guardaron alternativas, pero sus
    posiciones pueden seguir en la caché: se recuperan de ahí en vez de
    obligar a re-analizar la partida (ADR-0007).
    """
    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="no existe ese análisis")
    result = await session.execute(
        select(AnalyzedMove)
        .where(AnalyzedMove.analysis_id == analysis_id)
        .order_by(AnalyzedMove.ply)
    )
    moves = list(result.scalars().all())
    return analysis, moves, await alternatives_from_cache(session, analysis, moves)


@router.get("/analysis/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> AnalysisDetail:
    analysis, moves, cached_alternatives = await _load_analysis_with_moves(session, analysis_id)

    moves_out: list[AnalyzedMoveOut] = []
    for move in moves:
        serialized_alternatives = alternatives_of(move, cached_alternatives)
        move_out = AnalyzedMoveOut.model_validate(move)
        # La SAN de cada línea se nombra desde `fen_before`, que es justo la
        # posición de la que salieron las alternativas: se guardan con la
        # jugada, pero son de antes de jugarla.
        move_out.alternatives = [
            EngineLineOut.model_validate(line)
            for line in engine_lines_from_serialized(serialized_alternatives, move.fen_before)
        ]
        moves_out.append(move_out)

    return AnalysisDetail(
        **AnalysisSummary.model_validate(analysis).model_dump(),
        moves=moves_out,
        critical_moments=[
            CriticalMomentOut(
                ply=moment.ply,
                color=moment.color,
                san=moment.san,
                kinds=list(moment.kinds),
                win_percent_before=moment.win_percent_before,
                win_percent_after=moment.win_percent_after,
                best_alternative_san=moment.best_alternative_san,
            )
            for moment in analysis_critical_moments(moves, cached_alternatives)
        ],
    )


@router.get("/analysis/{analysis_id}/pgn", response_class=PlainTextResponse)
async def get_analysis_pgn(
    analysis_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> PlainTextResponse:
    """El PGN de la partida con las anotaciones del análisis (RF-5.5).

    Se descarga como archivo —de ahí el `Content-Disposition`— porque lo que
    se quiere hacer con él es abrirlo en lichess, ChessBase o SCID, no leerlo
    en el navegador.

    Solo se exporta un análisis **terminado**: uno a medias daría una partida
    comentada hasta la jugada 20 y muda a partir de ahí, que se lee como un
    archivo roto y no como un análisis en curso.
    """
    analysis, moves, cached_alternatives = await _load_analysis_with_moves(session, analysis_id)
    if analysis.status != "done":
        raise HTTPException(
            status_code=409,
            detail=f"el análisis todavía no está terminado (está «{analysis.status}»)",
        )
    game = await session.get(Game, analysis.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="no existe la partida de ese análisis")

    annotated_pgn = export_annotated_pgn(game, analysis, moves, cached_alternatives)
    filename = _pgn_download_filename(game)
    return PlainTextResponse(
        annotated_pgn,
        media_type="application/x-chess-pgn",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pgn_download_filename(game: Game) -> str:
    """Nombre del archivo descargado: "lucia-blancas-negras-2026-03-14.pgn".

    Se reduce a ASCII y se limpia de todo lo que no sea letra, cifra o guion:
    el nombre viaja en una cabecera HTTP y acaba en el sistema de archivos del
    usuario, y los nombres de los jugadores traen acentos, comas y espacios.
    """

    def slugify(text: str) -> str:
        ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
        return re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-").lower() or "partida"

    played_on = game.played_at.date().isoformat()
    return f"lucia-{slugify(game.white_username)}-{slugify(game.black_username)}-{played_on}.pgn"


@router.websocket("/ws/analysis/{analysis_id}")
async def analysis_progress(
    websocket: WebSocket,
    analysis_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Progreso en vivo de un análisis (RF-2.4). Si el análisis ya había
    terminado antes de conectar, se envía el resultado final una vez y se
    cierra. Nota: queda una ventana de carrera muy pequeña, entre suscribirse
    y volver a comprobar el estado, en la que un evento final podría
    perderse; para ese caso, `GET /analysis/{id}` siempre tiene el estado
    real como respaldo."""
    worker: AnalysisWorker = websocket.app.state.worker
    await websocket.accept()

    analysis = await session.get(Analysis, analysis_id)
    if analysis is None:
        await websocket.send_json({"status": "error", "error": "no existe ese análisis"})
        await websocket.close()
        return
    if analysis.status in ("done", "error"):
        await websocket.send_json({"status": analysis.status, "error": analysis.error})
        await websocket.close()
        return

    progress_queue = worker.subscribe(analysis_id)
    try:
        await session.refresh(analysis)
        if analysis.status in ("done", "error"):
            await websocket.send_json({"status": analysis.status, "error": analysis.error})
            return
        while True:
            event = await progress_queue.get()
            await websocket.send_json(event)
            if event["status"] in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        worker.unsubscribe(analysis_id, progress_queue)

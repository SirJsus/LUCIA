"""POST /analysis, GET /analysis/{id}, WS /ws/analysis/{id} — analizar
partidas con motor (RF-2) usando `lucia-core` como librería."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.dependencies import get_worker
from lucia_api.services.analysis import analyse_position
from lucia_api.services.comparison import (
    DEFAULT_DISAGREEMENT_THRESHOLD,
    ComparisonError,
    compare_analyses,
)
from lucia_api.services.engines import get_effective_config
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
    game_id: int
    engine: str
    depth: int
    multipv: int
    status: str
    error: str | None
    white_accuracy: float | None
    black_accuracy: float | None


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


class AnalysisDetail(AnalysisSummary):
    moves: list[AnalyzedMoveOut]


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
    config_motor = await get_effective_config(session, body.engine)

    creadas: list[Analysis] = []
    for game_id in body.game_ids:
        juego = await session.get(Game, game_id)
        if juego is None:
            raise HTTPException(status_code=404, detail=f"no existe la partida {game_id}")
        analisis = Analysis(
            game_id=game_id,
            engine=body.engine,
            depth=body.depth or config_motor.depth,
            multipv=body.multipv or config_motor.multipv,
        )
        session.add(analisis)
        creadas.append(analisis)
    await session.commit()

    for analisis in creadas:
        await worker.enqueue(analisis.id)

    return [AnalysisSummary.model_validate(a) for a in creadas]


class PositionAnalysisRequest(BaseModel):
    fen: str
    engine: Literal["stockfish", "lc0"] = "stockfish"
    depth: int | None = Field(default=None, ge=1, le=MAX_LIVE_DEPTH)
    """Acotado: este endpoint responde de forma síncrona, y una profundidad
    alta dejaría la petición colgada minutos."""
    multipv: int | None = Field(default=None, ge=1, le=10)


class EngineLineOut(BaseModel):
    rank: int
    score_cp: int | None
    score_mate: int | None
    pv_uci: list[str]
    pv_san: list[str]


@router.post("/analysis/position", response_model=list[EngineLineOut])
async def analyze_position(
    body: PositionAnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EngineLineOut]:
    """Analiza una posición suelta y devuelve las mejores líneas (RF-5.2 /
    RF-6.2). Para el tablero de análisis y la exploración en vivo."""
    try:
        lineas = await analyse_position(
            session, body.fen, engine_name=body.engine, depth=body.depth, multipv=body.multipv
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"FEN inválido: {error}") from error
    return [
        EngineLineOut(
            rank=linea.rank,
            score_cp=linea.score_cp,
            score_mate=linea.score_mate,
            pv_uci=linea.pv_uci,
            pv_san=linea.pv_san,
        )
        for linea in lineas
    ]


@router.get("/analysis", response_model=list[AnalysisSummary])
async def list_analyses(
    session: Annotated[AsyncSession, Depends(get_session)],
    game_id: int | None = None,
) -> list[AnalysisSummary]:
    """Análisis existentes, opcionalmente los de una partida concreta. Sirve
    para que el visor sepa si ya hay uno hecho en vez de volver a analizar."""
    consulta = select(Analysis).order_by(Analysis.created_at.desc())
    if game_id is not None:
        consulta = consulta.where(Analysis.game_id == game_id)
    resultado = await session.execute(consulta)
    return [AnalysisSummary.model_validate(a) for a in resultado.scalars().all()]


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
        comparacion = await compare_analyses(session, analysis_a, analysis_b, threshold)
    except ComparisonError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return AnalysisComparisonOut(
        game_id=comparacion.game_id,
        analysis_a=comparacion.analysis_a,
        analysis_b=comparacion.analysis_b,
        engine_a=comparacion.engine_a,
        engine_b=comparacion.engine_b,
        total_moves=comparacion.total_moves,
        agreed_best_moves=comparacion.agreed_best_moves,
        best_move_agreement_percent=comparacion.best_move_agreement_percent,
        disagreements=[
            MoveComparisonOut(
                ply=d.ply,
                color=d.color,
                san=d.san,
                classification_a=d.classification_a,
                classification_b=d.classification_b,
                win_percent_after_a=d.win_percent_after_a,
                win_percent_after_b=d.win_percent_after_b,
                win_percent_gap=d.win_percent_gap,
                best_move_a=d.best_move_a,
                best_move_b=d.best_move_b,
                same_best_move=d.same_best_move,
            )
            for d in comparacion.disagreements
        ],
    )


@router.get("/analysis/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> AnalysisDetail:
    analisis = await session.get(Analysis, analysis_id)
    if analisis is None:
        raise HTTPException(status_code=404, detail="no existe ese análisis")
    resultado = await session.execute(
        select(AnalyzedMove)
        .where(AnalyzedMove.analysis_id == analysis_id)
        .order_by(AnalyzedMove.ply)
    )
    jugadas = resultado.scalars().all()
    return AnalysisDetail(
        **AnalysisSummary.model_validate(analisis).model_dump(),
        moves=[AnalyzedMoveOut.model_validate(j) for j in jugadas],
    )


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

    analisis = await session.get(Analysis, analysis_id)
    if analisis is None:
        await websocket.send_json({"status": "error", "error": "no existe ese análisis"})
        await websocket.close()
        return
    if analisis.status in ("done", "error"):
        await websocket.send_json({"status": analisis.status, "error": analisis.error})
        await websocket.close()
        return

    cola = worker.subscribe(analysis_id)
    try:
        await session.refresh(analisis)
        if analisis.status in ("done", "error"):
            await websocket.send_json({"status": analisis.status, "error": analisis.error})
            return
        while True:
            evento = await cola.get()
            await websocket.send_json(evento)
            if evento["status"] in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        worker.unsubscribe(analysis_id, cola)

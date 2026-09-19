"""CRUD de tableros de análisis (RF-6.1 a RF-6.9).

El árbol de variantes viaja como JSON opaco: la forma la define el front
(`apps/web/src/features/board/tree.ts`), que es quien tiene chess.js para
validar jugadas. Aquí solo se comprueba que sea un objeto y que el FEN raíz
sea legal, para no guardar un tablero que después no se pueda abrir.

El historial de deshacer y rehacer (RF-6.8) vive en `services/boards.py`: cada
escritura que cambia el árbol anota una versión, y `POST /boards/{id}/undo` y
`/redo` mueven el cursor por ellas.

`PUT /boards/{id}/own-game` y `DELETE` (RF-6.5) publican el tablero en el
historial como partida propia y retiran la marca; quién la publica y con qué
datos está en `services/own_games.py`.

`POST /boards/{id}/analysis` (RF-6.9) encola el análisis de la línea principal
en el mismo worker que las partidas: la corrida de motor es idéntica, y lo
único propio es que el PGN lo manda el front —aquí no se sabe recorrer el
árbol— y se guarda con el análisis, porque el tablero se sigue editando
después.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any, Literal

import chess
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.db.models import Analysis, Board, BoardVersion
from lucia_api.dependencies import get_worker, resolved_username
from lucia_api.routers.analysis import AnalysisSummary
from lucia_api.services.boards import (
    can_redo,
    can_undo,
    record_version,
    restore_next_version,
    restore_previous_version,
)
from lucia_api.services.engines import get_effective_config
from lucia_api.services.own_games import (
    OwnGameDetails,
    get_own_game_with_details,
    link_analyses_to_own_game,
    publish_board_as_own_game,
    refresh_own_game_moves,
    unpublish_own_game,
)
from lucia_api.worker import AnalysisWorker

router = APIRouter(tags=["boards"])


class BoardSummary(BaseModel):
    """Lo que hace falta para listar; sin el árbol, que puede ser grande."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    tags_json: list | None
    root_fen: str
    is_own_game: bool
    created_at: dt.datetime
    updated_at: dt.datetime


class OwnGameLink(OwnGameDetails):
    """La partida del historial en la que está publicado el tablero (RF-6.5).

    Lleva los datos con los que se publicó para que la pantalla los vuelva a
    enseñar tal cual al corregirlos, y el `game_id` para poder abrirla en el
    visor como cualquier otra partida."""

    game_id: int


class BoardDetail(BoardSummary):
    tree_json: dict
    can_undo: bool
    """Si hay una versión anterior a la que volver (RF-6.8). Va en la
    respuesta y no se deduce en la pantalla porque el historial está en la
    base: el front no sabe cuántas versiones hay."""
    can_redo: bool
    own_game: OwnGameLink | None = None
    """`None` mientras el tablero no esté marcado como partida propia."""


class BoardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    root_fen: str = chess.STARTING_FEN
    tree_json: dict[str, Any] = Field(default_factory=dict)
    tags_json: list[str] | None = None


class BoardUpdate(BaseModel):
    """Todos los campos son opcionales: la UI autoguarda solo lo que cambió."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    root_fen: str | None = None
    """Cambia al importar un PGN que arranca de una posición dada (RF-6.7):
    el árbol nuevo cuelga de otra raíz, y dejar aquí la anterior haría que el
    listado de tableros enseñara una posición que ya no es la suya."""
    tree_json: dict[str, Any] | None = None
    tags_json: list[str] | None = None
    pgn: str | None = None
    """La línea que hay ahora en el tablero, tal como la exporta
    `tree.ts::toPgn`. Solo hace falta cuando el tablero está publicado como
    partida propia (RF-6.5): es lo que mantiene al día la fila de `games` y lo
    que dice si su análisis sigue siendo el de estas jugadas. Se ignora en los
    demás, que son casi todos."""


async def _get_board(session: AsyncSession, board_id: int) -> Board:
    board = await session.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="no existe ese tablero")
    return board


def _validate_fen(fen: str) -> None:
    try:
        chess.Board(fen)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"FEN inválido: {error}") from error


@router.get("/boards", response_model=list[BoardSummary])
async def list_boards(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BoardSummary]:
    result = await session.execute(
        select(Board).order_by(Board.updated_at.desc()).limit(limit).offset(offset)
    )
    return [BoardSummary.model_validate(board) for board in result.scalars().all()]


async def _board_detail(session: AsyncSession, board: Board) -> BoardDetail:
    """El tablero con los dos avisos que dependen del historial."""
    published = await get_own_game_with_details(session, board)
    return BoardDetail(
        **BoardSummary.model_validate(board).model_dump(),
        tree_json=board.tree_json,
        can_undo=await can_undo(session, board),
        can_redo=await can_redo(session, board),
        own_game=(
            OwnGameLink(game_id=published[0].id, **published[1].model_dump()) if published else None
        ),
    )


@router.post("/boards", response_model=BoardDetail, status_code=201)
async def create_board(
    body: BoardCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    _validate_fen(body.root_fen)
    board = Board(
        title=body.title,
        root_fen=body.root_fen,
        tree_json=body.tree_json,
        tags_json=body.tags_json,
    )
    session.add(board)
    await session.flush()
    # El estado de partida es la primera versión: sin ella, deshacer la
    # primera jugada no tendría adónde volver.
    await record_version(session, board)
    await session.commit()
    return await _board_detail(session, board)


@router.get("/boards/{board_id}", response_model=BoardDetail)
async def get_board(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    board = await _get_board(session, board_id)
    return await _board_detail(session, board)


@router.put("/boards/{board_id}", response_model=BoardDetail)
async def update_board(
    board_id: int,
    body: BoardUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BoardDetail:
    board = await _get_board(session, board_id)
    board_content_changed = body.tree_json is not None or body.root_fen is not None

    if body.title is not None:
        board.title = body.title
    if body.root_fen is not None:
        _validate_fen(body.root_fen)
        board.root_fen = body.root_fen
    if body.tree_json is not None:
        board.tree_json = body.tree_json
    if body.tags_json is not None:
        board.tags_json = body.tags_json
    board.updated_at = dt.datetime.now(dt.UTC)

    # Si el tablero está publicado como partida propia, la fila de `games`
    # sigue a las jugadas: sin esto el historial enseñaría una partida que ya
    # no es la de este tablero (RF-6.5). Se exige el PGN en vez de dejar la
    # partida atrasada en silencio, que es el fallo que nadie ve.
    if board_content_changed and board.is_own_game:
        if body.pgn is None:
            raise HTTPException(
                status_code=422,
                detail="este tablero está publicado como partida propia: manda también su pgn",
            )
        await refresh_own_game_moves(session, board, body.pgn)

    # Solo lo que cambia el árbol hace historial: renombrar el tablero o
    # marcarlo como partida propia no es algo que se deshaga con Ctrl+Z, y
    # anotarlo obligaría a pulsar dos veces para retirar una jugada.
    if board_content_changed:
        await record_version(session, board, body.pgn)

    await session.commit()
    return await _board_detail(session, board)


@router.post("/boards/{board_id}/undo", response_model=BoardDetail)
async def undo_board(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    """Devuelve el tablero a su estado anterior (RF-6.8).

    409 y no 400 cuando no hay nada que deshacer: la petición es correcta, es
    el estado del tablero el que no la admite.
    """
    board = await _get_board(session, board_id)
    restored = await restore_previous_version(session, board)
    if restored is None:
        raise HTTPException(status_code=409, detail="no hay nada que deshacer")
    await _follow_own_game_to(session, board, restored)
    await session.commit()
    return await _board_detail(session, board)


@router.post("/boards/{board_id}/redo", response_model=BoardDetail)
async def redo_board(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    board = await _get_board(session, board_id)
    restored = await restore_next_version(session, board)
    if restored is None:
        raise HTTPException(status_code=409, detail="no hay nada que rehacer")
    await _follow_own_game_to(session, board, restored)
    await session.commit()
    return await _board_detail(session, board)


class OwnGamePublishRequest(OwnGameDetails):
    """Marcar el tablero como partida propia (RF-6.5): los datos que el
    tablero no tiene, más las jugadas que sí."""

    pgn: str = Field(min_length=1)
    """El tablero en PGN, tal como lo exporta `tree.ts::toPgn`. Viene del
    front y no se deduce aquí por la misma razón que en el análisis: recorrer
    el árbol es cosa de chess.js."""


@router.put("/boards/{board_id}/own-game", response_model=BoardDetail)
async def publish_own_game(
    board_id: int,
    body: OwnGamePublishRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BoardDetail:
    """Publica el tablero en el historial como partida propia (RF-6.5).

    A partir de aquí cuenta en el dashboard, en los patrones y en los filtros
    del listado como cualquier otra partida. La misma llamada sirve para
    corregir los datos y para poner al día las jugadas después de deshacer o
    rehacer: reescribe la partida publicada en vez de crear otra.
    """
    board = await _get_board(session, board_id)
    # `OwnGamePublishRequest` es un `OwnGameDetails` con el PGN al lado: se
    # pasa tal cual, sin volver a validar los mismos campos.
    await publish_board_as_own_game(
        session,
        board,
        details=body,
        username=resolved_username(body.username),
        pgn=body.pgn,
    )
    await session.commit()
    return await _board_detail(session, board)


@router.delete("/boards/{board_id}/own-game", response_model=BoardDetail)
async def withdraw_own_game(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> BoardDetail:
    """Retira la marca de partida propia: el tablero deja de contar y su
    partida se va del historial (RF-6.5). El tablero se queda como estaba."""
    board = await _get_board(session, board_id)
    await unpublish_own_game(session, board)
    await session.commit()
    return await _board_detail(session, board)


async def _follow_own_game_to(session: AsyncSession, board: Board, restored: BoardVersion) -> None:
    """Tras deshacer o rehacer, la partida publicada sigue al tablero (RF-6.5).

    Deshacer cambia las jugadas, y el historial es lo que el usuario jugó: si
    la fila de `games` se quedara con las de antes, el visor enseñaría una
    partida que ya no es la de este tablero. El PGN sale de la versión
    restaurada, que lo guarda desde RF-6.5 precisamente para esto: aquí no se
    sabe recorrer el árbol.

    En una versión anterior a esa columna no hay PGN que aplicar, así que lo
    único que se puede hacer sin inventar nada es desenlazar el análisis —deja
    de contar en las estadísticas— hasta el siguiente guardado.
    """
    if not board.is_own_game:
        return
    if restored.pgn is None:
        await link_analyses_to_own_game(session, board, analyzed_pgn=None)
        return
    await refresh_own_game_moves(session, board, restored.pgn)


class BoardAnalysisRequest(BaseModel):
    """Lo que hace falta para analizar la línea principal de un tablero
    (RF-6.9)."""

    pgn: str = Field(min_length=1)
    """La línea principal en PGN, tal como la exporta `tree.ts::toPgn`. Viene
    del front y no se deduce aquí: recorrer el árbol es cosa de chess.js, que
    es quien sabe de jugadas legales."""
    engine: Literal["stockfish", "lc0"] = "stockfish"
    depth: int | None = None
    multipv: int | None = None


@router.post("/boards/{board_id}/analysis", response_model=AnalysisSummary, status_code=201)
async def analyze_board(
    board_id: int,
    body: BoardAnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    worker: Annotated[AnalysisWorker, Depends(get_worker)],
) -> AnalysisSummary:
    """Encola el análisis completo de la línea principal del tablero (RF-6.9).

    Devuelve en cuanto está en la cola, con el id que el front usa para
    seguir el progreso por `WS /ws/analysis/{id}`, igual que una partida. El
    análisis **no cuenta en las estadísticas** salvo que el tablero esté
    publicado como partida propia (RF-6.5), que es cuando nace con `game_id`.
    """
    board = await _get_board(session, board_id)  # 404 antes de encolar nada

    # Si el tablero está publicado como partida propia, lo que se va a
    # analizar son las jugadas de esa partida: se ponen al día y el análisis
    # nuevo nace ya enlazado a ella, para que cuente en cuanto termine
    # (RF-6.5).
    if board.is_own_game:
        await refresh_own_game_moves(session, board, body.pgn)

    # Sin `depth`/`multipv` explícitos, los que el usuario dejó configurados
    # en /engines/config (RF-5.4), como en el análisis de una partida.
    effective_config = await get_effective_config(session, body.engine)
    analysis = Analysis(
        board_id=board_id,
        game_id=board.own_game_id,
        analyzed_pgn=body.pgn,
        engine=body.engine,
        depth=body.depth or effective_config.depth,
        multipv=body.multipv or effective_config.multipv,
    )
    session.add(analysis)
    await session.commit()
    await worker.enqueue(analysis.id)
    return AnalysisSummary.model_validate(analysis)


@router.delete("/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    board = await _get_board(session, board_id)
    # La partida publicada se va con el tablero: sin él no hay jugadas que
    # describir, igual que sus análisis y sus versiones (RF-6.5).
    await unpublish_own_game(session, board)
    await session.delete(board)
    await session.commit()

"""Historial de un tablero de análisis: deshacer y rehacer (RF-6.8).

El tablero guarda su estado actual en `boards.tree_json` —eso es lo que la
pantalla carga y lo que el autoguardado escribe— y aquí se lleva aparte la
lista de estados por los que pasó, en `board_versions`. Las dos cosas se
escriben en la misma operación: `record_version` es lo que llama
`PUT /boards/{id}` cada vez que el árbol cambia.

**El historial es lineal**, como el de un editor de texto: `Board
.current_version_id` dice dónde está el cursor, deshacer lo mueve hacia atrás
sin borrar nada, y la primera edición después de deshacer descarta lo que
quedaba por delante. Un historial en árbol sería más potente, pero explicarlo
en una pantalla que ya tiene un árbol de variantes sería pedirle demasiado a
quien solo quería retirar una jugada.

Aquí no se interpreta el árbol: igual que en `routers/boards.py`, el
`tree_json` es un documento que se guarda y se devuelve, y quien sabe de
reglas de ajedrez es chess.js en el front.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Board, BoardVersion

#: Cuántos estados se conservan por tablero. Al pasarse, se tiran los más
#: antiguos. Cincuenta cubre de sobra "deshaz lo que acabas de hacer", que es
#: para lo que se usa esto, sin que un tablero muy trabajado acumule miles de
#: copias de su propio árbol.
MAX_VERSIONS_PER_BOARD = 50


async def record_version(
    session: AsyncSession, board: Board, pgn: str | None = None
) -> BoardVersion:
    """Anota el estado actual del tablero como una versión más y deja el
    cursor en ella.

    `pgn` es ese mismo estado compuesto por el front (`tree.ts::toPgn`). Se
    guarda con la versión porque aquí no se sabe recorrer el árbol, y al
    deshacer hace falta para poner al día la partida de un tablero publicado
    como propio (RF-6.5). Sin él la versión se anota igual; lo que se pierde es
    poder reconstruir su PGN después.

    Se llama **después** de haber escrito los campos nuevos en `board`, no
    antes: la versión que se anota es la que acaba de quedar, de modo que el
    cursor siempre apunta a lo que la pantalla está enseñando.

    Si se había deshecho algo, lo que quedaba por delante se descarta aquí:
    esa rama del historial ya no lleva a ningún sitio al que se pueda volver.
    """
    await _discard_versions_after_cursor(session, board)

    version = BoardVersion(
        board_id=board.id, root_fen=board.root_fen, tree_json=board.tree_json, pgn=pgn
    )
    session.add(version)
    await session.flush()  # hace falta el id para dejar el cursor aquí
    board.current_version_id = version.id

    await _prune_oldest_versions(session, board)
    return version


async def restore_previous_version(session: AsyncSession, board: Board) -> BoardVersion | None:
    """Devuelve el tablero a la versión anterior, y esa versión. `None` si no
    hay ninguna.

    Devuelve la versión y no un `bool` porque quien llama necesita su `pgn`:
    es con lo que un tablero publicado como partida propia pone al día su fila
    del historial (RF-6.5)."""
    return await _move_cursor_to(session, board, await _adjacent_version(session, board, back=True))


async def restore_next_version(session: AsyncSession, board: Board) -> BoardVersion | None:
    """Rehace lo último deshecho, y devuelve esa versión. `None` si el cursor
    ya está al día."""
    return await _move_cursor_to(
        session, board, await _adjacent_version(session, board, back=False)
    )


async def can_undo(session: AsyncSession, board: Board) -> bool:
    return await _adjacent_version(session, board, back=True) is not None


async def can_redo(session: AsyncSession, board: Board) -> bool:
    return await _adjacent_version(session, board, back=False) is not None


async def _adjacent_version(
    session: AsyncSession, board: Board, *, back: bool
) -> BoardVersion | None:
    """La versión inmediatamente anterior o posterior al cursor.

    El orden es por `id` y no por `created_at` porque el id es monótono y no
    empata: dos versiones guardadas en el mismo segundo tienen la misma fecha,
    y deshacer entre ellas se quedaría dando vueltas.
    """
    if board.current_version_id is None:
        return None
    versions = select(BoardVersion).where(BoardVersion.board_id == board.id)
    query = (
        versions.where(BoardVersion.id < board.current_version_id).order_by(BoardVersion.id.desc())
        if back
        else versions.where(BoardVersion.id > board.current_version_id).order_by(BoardVersion.id)
    )
    return (await session.execute(query.limit(1))).scalar_one_or_none()


async def _move_cursor_to(
    session: AsyncSession, board: Board, version: BoardVersion | None
) -> BoardVersion | None:
    """Deja el tablero como estaba en esa versión y la devuelve. La versión
    **no** se borra: es lo que permite volver en la otra dirección."""
    if version is None:
        return None
    board.root_fen = version.root_fen
    board.tree_json = version.tree_json
    board.current_version_id = version.id
    board.updated_at = dt.datetime.now(dt.UTC)
    return version


async def _discard_versions_after_cursor(session: AsyncSession, board: Board) -> None:
    if board.current_version_id is None:
        return
    await session.execute(
        delete(BoardVersion).where(
            BoardVersion.board_id == board.id,
            BoardVersion.id > board.current_version_id,
        )
    )


async def _prune_oldest_versions(session: AsyncSession, board: Board) -> None:
    """Deja el historial en `MAX_VERSIONS_PER_BOARD` tirando por el principio.

    Nunca puede tocar el cursor: se poda desde la más antigua y el cursor
    acaba de quedar en la más nueva.
    """
    newest = (
        select(BoardVersion.id)
        .where(BoardVersion.board_id == board.id)
        .order_by(BoardVersion.id.desc())
        .limit(MAX_VERSIONS_PER_BOARD)
    )
    await session.execute(
        delete(BoardVersion)
        .where(BoardVersion.board_id == board.id, BoardVersion.id.not_in(newest))
        # Sin sincronizar la sesión: las versiones que se tiran son las más
        # antiguas y nadie las tiene en la mano; comprobarlo obligaría a
        # traerlas antes de borrarlas, que es justo lo que se evita.
        .execution_options(synchronize_session=False)
    )

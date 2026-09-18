"""POST /import/pgn — importar partidas desde un archivo PGN (RF-1.5)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import resolved_username
from lucia_api.services.pgn_import import PgnImportSummary, import_pgn

router = APIRouter(tags=["import"])

#: Tope del archivo subido. Un PGN es texto plano: 5 MB son decenas de miles
#: de partidas, muy por encima de cualquier archivo de torneo, así que una
#: subida más grande es una equivocación y se rechaza antes de leerla entera
#: en memoria.
MAX_PGN_BYTES = 5 * 1024 * 1024


@router.post("/import/pgn", response_model=PgnImportSummary)
async def import_pgn_file(
    session: Annotated[AsyncSession, Depends(get_session)],
    file: Annotated[UploadFile, File(description="Archivo .pgn con una o varias partidas")],
    username: Annotated[str | None, Form()] = None,
    player_name_in_pgn: Annotated[str | None, Form()] = None,
) -> PgnImportSummary:
    """Guarda en el historial las partidas del archivo (RF-1.5).

    - `username`: a quién se le atribuyen; si se omite, `CHESSCOM_USERNAME`.
    - `player_name_in_pgn`: **cómo aparece ese jugador dentro del PGN**. Un archivo de
      torneo lo nombra "Durán, Jesús" y no con su usuario, así que sin esto la
      partida se guarda pero no cuenta en el dashboard ni en los filtros por
      color, resultado o rival, que casan por nombre. El PGN se guarda entero,
      de modo que el nombre original no se pierde.

    Las partidas repetidas no se duplican: se identifican por el contenido del
    PGN, así que reimportar el mismo archivo reescribe las mismas filas.
    """
    if file.size and file.size > MAX_PGN_BYTES:
        raise HTTPException(
            status_code=413, detail=f"el archivo pasa de {MAX_PGN_BYTES // 1024 // 1024} MB"
        )
    raw_pgn = await file.read()
    try:
        pgn_text = raw_pgn.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Los PGN viejos de programas de escritorio suelen venir en Latin-1.
        pgn_text = raw_pgn.decode("latin-1")

    summary = await import_pgn(
        session,
        pgn_text,
        username=resolved_username(username),
        player_name_in_pgn=player_name_in_pgn or None,
    )
    if not summary.games_imported and not summary.games_already_present:
        raise HTTPException(
            status_code=422,
            detail="; ".join(summary.skipped_game_reasons) or "el archivo no trae ninguna partida",
        )
    return summary

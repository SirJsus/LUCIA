"""POST /sync — importar/actualizar partidas desde chess.com (RF-1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from lucia_chesscom import ChessComClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db import get_session
from lucia_api.dependencies import get_chesscom_client
from lucia_api.services.chesscom_sync import SyncSummary, sync_player
from lucia_api.settings import settings

router = APIRouter(tags=["sync"])


class SyncRequest(BaseModel):
    username: str | None = None
    """Si se omite, usa CHESSCOM_USERNAME de la configuración."""


@router.post("/sync", response_model=SyncSummary)
async def sync(
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[ChessComClient, Depends(get_chesscom_client)],
    body: SyncRequest | None = None,
) -> SyncSummary:
    username = (body.username if body else None) or settings.chesscom_username
    return await sync_player(session, client, username)

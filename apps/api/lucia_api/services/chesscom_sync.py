"""Servicio de sincronización con chess.com (RF-1): orquesta
`lucia_chesscom` y persiste en SQLite (flujo "Sincronizar" de
docs/03-arquitectura.md).
"""

from __future__ import annotations

import datetime as dt

from lucia_chesscom import ChessComClient, ChessComGame, parse_move_clocks
from lucia_chesscom.sync import months_to_sync
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Game, Player, SyncState


class SyncSummary(BaseModel):
    username: str
    months_synced: list[tuple[int, int]]
    games_upserted: int


async def sync_player(session: AsyncSession, client: ChessComClient, username: str) -> SyncSummary:
    player = await _get_or_create_player(session, client, username)
    sync_state = await session.get(SyncState, player.id)
    last_synced = (
        (sync_state.last_synced_year, sync_state.last_synced_month) if sync_state else None
    )

    archivos = await client.get_archives(username)
    meses_pendientes = months_to_sync(archivos, last_synced)

    games_upserted = 0
    for year, month in meses_pendientes:  # secuencial a propósito (RF-1.4)
        partidas = await client.get_month_games(username, year, month)
        for partida in partidas:
            await _upsert_game(session, player.id, year, month, partida)
            games_upserted += 1

    if meses_pendientes:
        era_nuevo = sync_state is None
        sync_state = _actualizar_sync_state(sync_state, player.id, meses_pendientes[-1])
        if era_nuevo:
            session.add(sync_state)

    await session.commit()
    return SyncSummary(
        username=username, months_synced=meses_pendientes, games_upserted=games_upserted
    )


async def _get_or_create_player(
    session: AsyncSession, client: ChessComClient, username: str
) -> Player:
    result = await session.execute(
        select(Player).where(Player.platform == "chesscom", Player.username == username)
    )
    player = result.scalar_one_or_none()

    perfil = await client.get_player(username)  # RF-1.1: país, fecha de alta
    stats = await client.get_stats(username)  # RF-1.6: ratings por control de tiempo
    joined_at = dt.datetime.fromtimestamp(perfil.joined, tz=dt.UTC)
    ratings_json = stats.model_dump(mode="json", exclude_none=True)

    if player is None:
        player = Player(
            platform="chesscom",
            username=username,
            country=perfil.country,
            joined_at=joined_at,
            ratings_json=ratings_json,
        )
        session.add(player)
        await session.flush()  # asigna player.id sin cerrar la transacción
    else:
        player.country = perfil.country
        player.joined_at = joined_at
        player.ratings_json = ratings_json
        player.fetched_at = dt.datetime.now(dt.UTC)

    return player


async def _upsert_game(
    session: AsyncSession, player_id: int, year: int, month: int, partida: ChessComGame
) -> None:
    platform_id = partida.uuid or partida.url
    result = await session.execute(
        select(Game).where(Game.platform == "chesscom", Game.platform_id == platform_id)
    )
    game = result.scalar_one_or_none()
    if game is None:
        game = Game(player_id=player_id, platform="chesscom", platform_id=platform_id)
        session.add(game)

    game.pgn = partida.pgn
    game.white_username = partida.white.username
    game.white_rating = partida.white.rating
    game.white_result = partida.white.result
    game.black_username = partida.black.username
    game.black_rating = partida.black.rating
    game.black_result = partida.black.result
    game.time_control = partida.time_control
    game.time_class = partida.time_class
    game.rules = partida.rules
    game.rated = partida.rated
    game.eco = partida.eco
    game.clocks_json = parse_move_clocks(partida.pgn)
    game.played_at = dt.datetime.fromtimestamp(partida.end_time, tz=dt.UTC)
    game.year = year
    game.month = month


def _actualizar_sync_state(
    sync_state: SyncState | None, player_id: int, ultimo_mes: tuple[int, int]
) -> SyncState:
    year, month = ultimo_mes
    if sync_state is None:
        sync_state = SyncState(player_id=player_id, last_synced_at=dt.datetime.now(dt.UTC))
    sync_state.last_synced_year = year
    sync_state.last_synced_month = month
    sync_state.last_synced_at = dt.datetime.now(dt.UTC)
    return sync_state

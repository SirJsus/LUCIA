"""Servicio de sincronización con chess.com (RF-1): orquesta
`lucia_chesscom` y persiste en SQLite (flujo "Sincronizar" de
docs/03-arquitectura.md).
"""

from __future__ import annotations

import datetime as dt

from lucia_chesscom import ChessComClient, ChessComGame, parse_move_clocks
from lucia_chesscom.sync import months_to_sync
from lucia_core.openings import opening_of_pgn
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

    available_archives = await client.get_archives(username)
    pending_months = months_to_sync(available_archives, last_synced)

    games_upserted = 0
    for year, month in pending_months:  # secuencial a propósito (RF-1.4)
        chesscom_games = await client.get_month_games(username, year, month)
        for chesscom_game in chesscom_games:
            await _upsert_game(session, player.id, year, month, chesscom_game)
            games_upserted += 1

    if pending_months:
        was_new = sync_state is None
        sync_state = _update_sync_state(sync_state, player.id, pending_months[-1])
        if was_new:
            session.add(sync_state)

    await session.commit()
    return SyncSummary(
        username=username, months_synced=pending_months, games_upserted=games_upserted
    )


async def _get_or_create_player(
    session: AsyncSession, client: ChessComClient, username: str
) -> Player:
    result = await session.execute(
        select(Player).where(Player.platform == "chesscom", Player.username == username)
    )
    player = result.scalar_one_or_none()

    profile = await client.get_player(username)  # RF-1.1: país, fecha de alta
    stats = await client.get_stats(username)  # RF-1.6: ratings por control de tiempo
    joined_at = dt.datetime.fromtimestamp(profile.joined, tz=dt.UTC)
    ratings_json = stats.model_dump(mode="json", exclude_none=True)

    if player is None:
        player = Player(
            platform="chesscom",
            username=username,
            country=profile.country,
            joined_at=joined_at,
            ratings_json=ratings_json,
        )
        session.add(player)
        await session.flush()  # asigna player.id sin cerrar la transacción
    else:
        player.country = profile.country
        player.joined_at = joined_at
        player.ratings_json = ratings_json
        player.fetched_at = dt.datetime.now(dt.UTC)

    return player


async def _upsert_game(
    session: AsyncSession, player_id: int, year: int, month: int, chesscom_game: ChessComGame
) -> None:
    platform_id = chesscom_game.uuid or chesscom_game.url
    result = await session.execute(
        select(Game).where(Game.platform == "chesscom", Game.platform_id == platform_id)
    )
    game = result.scalar_one_or_none()
    if game is None:
        game = Game(player_id=player_id, platform="chesscom", platform_id=platform_id)
        session.add(game)

    game.pgn = chesscom_game.pgn
    game.white_username = chesscom_game.white.username
    game.white_rating = chesscom_game.white.rating
    game.white_result = chesscom_game.white.result
    game.black_username = chesscom_game.black.username
    game.black_rating = chesscom_game.black.rating
    game.black_result = chesscom_game.black.result
    game.time_control = chesscom_game.time_control
    game.time_class = chesscom_game.time_class
    game.rules = chesscom_game.rules
    game.rated = chesscom_game.rated
    game.eco = chesscom_game.eco
    # La apertura propia, deducida de las jugadas: chess.com no la trae en
    # todas las partidas y nunca da el código ECO (RF-3.2).
    opening = opening_of_pgn(chesscom_game.pgn)
    game.opening_eco = opening.eco if opening else None
    game.opening_name = opening.name if opening else None
    game.clocks_json = parse_move_clocks(chesscom_game.pgn)
    game.played_at = dt.datetime.fromtimestamp(chesscom_game.end_time, tz=dt.UTC)
    game.year = year
    game.month = month


def _update_sync_state(
    sync_state: SyncState | None, player_id: int, latest_month: tuple[int, int]
) -> SyncState:
    year, month = latest_month
    if sync_state is None:
        sync_state = SyncState(player_id=player_id, last_synced_at=dt.datetime.now(dt.UTC))
    sync_state.last_synced_year = year
    sync_state.last_synced_month = month
    sync_state.last_synced_at = dt.datetime.now(dt.UTC)
    return sync_state

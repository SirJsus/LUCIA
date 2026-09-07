from collections.abc import Callable

from lucia_api.db.models import Game, Player, SyncState
from lucia_api.services.chesscom_sync import sync_player
from lucia_chesscom import ChessComGame
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# `ClientFactory` no referencia el tipo concreto `FakeChessComClient` a
# propósito: importarlo desde `conftest` reintroduciría exactamente la
# ambigüedad de paquete `tests` que `--import-mode=importlib` evita (ver
# docstring de `game_factory` en conftest.py). Solo importa la forma que
# `sync_player` necesita (duck typing), no la clase de prueba.
GameFactory = Callable[..., ChessComGame]
ClientFactory = Callable[..., object]


async def test_first_sync_creates_player_and_games(
    db_session: AsyncSession, game_factory: GameFactory, fake_chesscom_client: ClientFactory
) -> None:
    client = fake_chesscom_client(
        archives=[(2024, 1), (2024, 2)],
        games_by_month={
            (2024, 1): [game_factory(uuid="a1"), game_factory(uuid="a2")],
            (2024, 2): [game_factory(uuid="b1")],
        },
    )

    summary = await sync_player(db_session, client, "usuario_prueba")

    assert summary.months_synced == [(2024, 1), (2024, 2)]
    assert summary.games_upserted == 3

    player = (
        await db_session.execute(select(Player).where(Player.username == "usuario_prueba"))
    ).scalar_one()
    assert player.ratings_json["chess_rapid"]["last"]["rating"] == 1500
    assert player.country == "https://api.chess.com/pub/country/MX"
    assert player.joined_at is not None

    total_games = (await db_session.execute(select(func.count()).select_from(Game))).scalar_one()
    assert total_games == 3

    sync_state = (
        await db_session.execute(select(SyncState).where(SyncState.player_id == player.id))
    ).scalar_one()
    assert (sync_state.last_synced_year, sync_state.last_synced_month) == (2024, 2)


async def test_second_sync_only_fetches_new_months(
    db_session: AsyncSession, game_factory: GameFactory, fake_chesscom_client: ClientFactory
) -> None:
    first_client = fake_chesscom_client(
        archives=[(2024, 1)],
        games_by_month={(2024, 1): [game_factory(uuid="a1")]},
    )
    await sync_player(db_session, first_client, "usuario_prueba")

    second_client = fake_chesscom_client(
        archives=[(2024, 1), (2024, 3)],
        games_by_month={(2024, 3): [game_factory(uuid="c1"), game_factory(uuid="c2")]},
    )
    summary = await sync_player(db_session, second_client, "usuario_prueba")

    # (2024, 1) ya estaba sincronizado y no es el mes en curso: no se repite.
    assert summary.months_synced == [(2024, 3)]
    assert summary.games_upserted == 2

    total_games = (await db_session.execute(select(func.count()).select_from(Game))).scalar_one()
    assert total_games == 3  # a1 (de antes) + c1 + c2


async def test_resyncing_the_same_month_does_not_duplicate_games(
    db_session: AsyncSession, game_factory: GameFactory, fake_chesscom_client: ClientFactory
) -> None:
    client = fake_chesscom_client(
        archives=[(2024, 1)],
        games_by_month={(2024, 1): [game_factory(uuid="a1")]},
    )
    await sync_player(db_session, client, "usuario_prueba")
    # Repite la sincronización con exactamente el mismo estado de archivos:
    # como (2024, 1) ya es el último sincronizado, solo se reintenta si es el
    # mes en curso; aquí no lo es, así que no debería reprocesar nada.
    summary = await sync_player(db_session, client, "usuario_prueba")

    assert summary.months_synced == []
    assert summary.games_upserted == 0

    total_games = (await db_session.execute(select(func.count()).select_from(Game))).scalar_one()
    assert total_games == 1

from collections.abc import AsyncIterator, Callable

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.dependencies import get_chesscom_client
from lucia_api.main import app
from lucia_chesscom import ChessComGame
from sqlalchemy.ext.asyncio import AsyncSession

GameFactory = Callable[..., ChessComGame]
ClientFactory = Callable[..., object]


async def test_post_sync_devuelve_resumen(
    db_session: AsyncSession, game_factory: GameFactory, fake_chesscom_client: ClientFactory
) -> None:
    client = fake_chesscom_client(
        archives=[(2024, 1)],
        games_by_month={(2024, 1): [game_factory(uuid="a1")]},
    )

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _client() -> AsyncIterator[object]:
        yield client

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_chesscom_client] = _client
    try:
        with TestClient(app) as http:
            response = http.post("/sync", json={"username": "usuario_prueba"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "usuario_prueba"
    assert body["months_synced"] == [[2024, 1]]
    assert body["games_upserted"] == 1


async def test_post_sync_sin_body_usa_username_de_settings(
    db_session: AsyncSession,
    game_factory: GameFactory,
    fake_chesscom_client: ClientFactory,
    monkeypatch,
) -> None:
    monkeypatch.setattr("lucia_api.routers.sync.settings.chesscom_username", "de_la_config")
    client = fake_chesscom_client(archives=[], games_by_month={})

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _client() -> AsyncIterator[object]:
        yield client

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_chesscom_client] = _client
    try:
        with TestClient(app) as http:
            response = http.post("/sync", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["username"] == "de_la_config"

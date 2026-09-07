from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Game, Player
from lucia_api.main import app
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "a"]\n[Black "b"]\n[Result "1-0"]\n\n1. e4 e5 1-0\n'


async def _create_game(
    session: AsyncSession,
    *,
    platform_id: str,
    white: str,
    black: str,
    time_class: str = "blitz",
    rated: bool = True,
    days_ago: int = 0,
) -> Game:
    player = (
        await session.execute(select(Player).where(Player.username == white))
    ).scalar_one_or_none()
    if player is None:
        player = Player(platform="chesscom", username=white)
        session.add(player)
        await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id=platform_id,
        pgn=PGN,
        white_username=white,
        white_rating=1500,
        white_result="win",
        black_username=black,
        black_rating=1480,
        black_result="checkmated",
        time_control="180",
        time_class=time_class,
        rules="chess",
        rated=rated,
        played_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=days_ago),
        year=2024,
        month=1,
    )
    session.add(game)
    await session.commit()
    return game


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_list_games_orders_most_recent_first(db_session: AsyncSession) -> None:
    await _create_game(db_session, platform_id="g1", white="ana", black="beto", days_ago=5)
    await _create_game(db_session, platform_id="g2", white="ana", black="beto", days_ago=1)

    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/games")
        assert response.status_code == 200
        games = response.json()
        assert len(games) == 2
        assert games[0]["white_rating"] == 1500
        # la más reciente (days_ago=1) va primero
        played_at_dates = [p["played_at"] for p in games]
        assert played_at_dates == sorted(played_at_dates, reverse=True)
    finally:
        app.dependency_overrides.clear()


async def test_list_games_filters_by_username_and_color(db_session: AsyncSession) -> None:
    await _create_game(db_session, platform_id="g1", white="ana", black="beto")
    await _create_game(db_session, platform_id="g2", white="beto", black="ana")
    await _create_game(db_session, platform_id="g3", white="carla", black="dario")

    _override(db_session)
    try:
        with TestClient(app) as http:
            all_ana_games = http.get("/games", params={"username": "ana"}).json()
            only_white_games = http.get(
                "/games", params={"username": "ana", "color": "white"}
            ).json()
    finally:
        app.dependency_overrides.clear()

    assert len(all_ana_games) == 2
    assert len(only_white_games) == 1
    assert only_white_games[0]["white_username"] == "ana"


async def test_list_games_finds_the_player_regardless_of_case(
    db_session: AsyncSession,
) -> None:
    await _create_game(db_session, platform_id="g1", white="SirJsus", black="Rival")

    _override(db_session)
    try:
        with TestClient(app) as http:
            lowercase_games = http.get("/games", params={"username": "sirjsus"}).json()
            lowercase_white_games = http.get(
                "/games", params={"username": "sirjsus", "color": "white"}
            ).json()
    finally:
        app.dependency_overrides.clear()

    assert len(lowercase_games) == 1
    assert len(lowercase_white_games) == 1


async def test_list_games_filters_by_time_class_and_rated(db_session: AsyncSession) -> None:
    await _create_game(db_session, platform_id="g1", white="ana", black="beto", time_class="bullet")
    await _create_game(db_session, platform_id="g2", white="ana", black="beto", time_class="blitz")
    await _create_game(
        db_session, platform_id="g3", white="ana", black="beto", time_class="blitz", rated=False
    )

    _override(db_session)
    try:
        with TestClient(app) as http:
            blitz = http.get("/games", params={"time_class": "blitz"}).json()
            blitz_rated = http.get("/games", params={"time_class": "blitz", "rated": True}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(blitz) == 2
    assert len(blitz_rated) == 1


async def test_list_games_paginates_with_limit_and_offset(db_session: AsyncSession) -> None:
    for i in range(5):
        await _create_game(db_session, platform_id=f"g{i}", white="ana", black="beto", days_ago=i)

    _override(db_session)
    try:
        with TestClient(app) as http:
            page1 = http.get("/games", params={"limit": 2, "offset": 0}).json()
            page2 = http.get("/games", params={"limit": 2, "offset": 2}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(page1) == 2
    assert len(page2) == 2
    assert {p["played_at"] for p in page1}.isdisjoint({p["played_at"] for p in page2})


async def test_get_game_includes_pgn(db_session: AsyncSession) -> None:
    game = await _create_game(db_session, platform_id="g1", white="ana", black="beto")

    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get(f"/games/{game.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["pgn"] == PGN


async def test_get_game_with_unknown_id_returns_404(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/games/999999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

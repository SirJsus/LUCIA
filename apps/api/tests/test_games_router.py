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

# Partida de ventaja: empieza sin las torres blancas, y el PGN lo dice.
ODDS_PGN = (
    '[White "a"]\n[Black "b"]\n[Result "1-0"]\n[SetUp "1"]\n'
    '[FEN "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBN1 w kq - 0 1"]\n\n1. e4 e5 1-0\n'
)


async def _create_game(
    session: AsyncSession,
    *,
    platform_id: str,
    white: str,
    black: str,
    time_class: str = "blitz",
    rated: bool = True,
    days_ago: int = 0,
    pgn: str = PGN,
    platform: str = "chesscom",
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
        platform=platform,
        platform_id=platform_id,
        pgn=pgn,
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


async def test_list_games_flags_the_ones_from_a_custom_position(
    db_session: AsyncSession,
) -> None:
    """El listado tiene que poder avisar de una partida que no empieza en la
    posición estándar; si no, un tablero con piezas de menos parece un fallo."""
    standard = await _create_game(db_session, platform_id="normal", white="ana", black="beto")
    odds = await _create_game(
        db_session, platform_id="ventaja", white="ana", black="beto", pgn=ODDS_PGN
    )
    standard_id, odds_id = standard.id, odds.id

    _override(db_session)
    try:
        with TestClient(app) as http:
            games = {game["id"]: game for game in http.get("/games").json()}
    finally:
        app.dependency_overrides.clear()

    assert games[standard_id]["starts_from_custom_position"] is False
    assert games[odds_id]["starts_from_custom_position"] is True


async def test_list_games_filters_by_result_from_the_player_side(
    db_session: AsyncSession,
) -> None:
    """RF-5.3: "ganadas" depende de con qué color jugó cada uno, así que la
    misma partida es victoria para uno y derrota para el otro."""
    await _create_game(db_session, platform_id="won", white="ana", black="beto")
    await _create_game(db_session, platform_id="lost", white="beto", black="ana")
    _override(db_session)
    try:
        with TestClient(app) as http:
            ana_wins = http.get("/games", params={"username": "ana", "result": "win"}).json()
            beto_wins = http.get("/games", params={"username": "beto", "result": "win"}).json()
            ana_losses = http.get("/games", params={"username": "ana", "result": "loss"}).json()
    finally:
        app.dependency_overrides.clear()

    # `_create_game` deja siempre ganando a las blancas.
    assert [game["white_username"] for game in ana_wins] == ["ana"]
    assert [game["white_username"] for game in beto_wins] == ["beto"]
    assert [game["black_username"] for game in ana_losses] == ["ana"]


async def test_list_games_filters_by_opponent(db_session: AsyncSession) -> None:
    await _create_game(db_session, platform_id="vs-beto", white="ana", black="beto")
    await _create_game(db_session, platform_id="vs-caro", white="caro", black="ana")
    _override(db_session)
    try:
        with TestClient(app) as http:
            versus_caro = http.get("/games", params={"username": "ana", "opponent": "caro"}).json()
    finally:
        app.dependency_overrides.clear()

    # El rival está al otro lado del tablero, juegue ana de blancas o de negras.
    assert len(versus_caro) == 1
    assert versus_caro[0]["white_username"] == "caro"


async def test_a_filter_that_needs_a_player_is_ignored_without_one(
    db_session: AsyncSession,
) -> None:
    """Sin `username`, "ganadas" o "contra fulano" no significan nada: se
    ignoran en vez de devolver algo plausible y equivocado."""
    await _create_game(db_session, platform_id="una", white="ana", black="beto")
    _override(db_session)
    try:
        with TestClient(app) as http:
            without_player = http.get("/games", params={"result": "loss"}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(without_player) == 1


async def test_list_games_filters_by_opening_substring(db_session: AsyncSession) -> None:
    """Buscar "sicilian" trae todas las sicilianas, no solo la variante que se
    escriba entera."""
    najdorf = await _create_game(db_session, platform_id="naj", white="ana", black="beto")
    najdorf.opening_name = "Sicilian Defense: Najdorf Variation"
    dragon = await _create_game(db_session, platform_id="dra", white="ana", black="beto")
    dragon.opening_name = "Sicilian Defense: Dragon Variation"
    italian = await _create_game(db_session, platform_id="ita", white="ana", black="beto")
    italian.opening_name = "Italian Game"
    await db_session.commit()

    _override(db_session)
    try:
        with TestClient(app) as http:
            sicilians = http.get("/games", params={"opening": "sicilian"}).json()
            najdorfs = http.get("/games", params={"opening": "najdorf"}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(sicilians) == 2
    assert len(najdorfs) == 1


async def test_list_games_filters_by_date_range(db_session: AsyncSession) -> None:
    """El día de `until` cuenta entero: quien filtra "hasta hoy" espera las de
    hoy, no las de hasta su medianoche."""
    await _create_game(db_session, platform_id="hoy", white="ana", black="beto", days_ago=0)
    await _create_game(db_session, platform_id="ayer", white="ana", black="beto", days_ago=1)
    await _create_game(db_session, platform_id="hace-10", white="ana", black="beto", days_ago=10)
    today = dt.datetime.now(dt.UTC).date()

    _override(db_session)
    try:
        with TestClient(app) as http:
            since_yesterday = http.get(
                "/games", params={"since": str(today - dt.timedelta(days=1))}
            ).json()
            until_yesterday = http.get(
                "/games", params={"until": str(today - dt.timedelta(days=1))}
            ).json()
    finally:
        app.dependency_overrides.clear()

    assert len(since_yesterday) == 2  # la de hoy y la de ayer
    assert len(until_yesterday) == 2  # la de ayer y la de hace diez días


async def test_list_games_reports_how_many_match_the_filters(
    db_session: AsyncSession,
) -> None:
    """La cabecera `X-Total-Count` cuenta las que cumplen los filtros, no las
    de la página: es lo que permite decir "25 de 324" en vez de solo "página 2"."""
    for index in range(5):
        await _create_game(db_session, platform_id=f"p{index}", white="ana", black="beto")
    _override(db_session)
    try:
        with TestClient(app) as http:
            page = http.get("/games", params={"limit": 2})
            filtered = http.get("/games", params={"username": "nadie"})
    finally:
        app.dependency_overrides.clear()

    assert len(page.json()) == 2
    assert page.headers["X-Total-Count"] == "5"
    assert filtered.headers["X-Total-Count"] == "0"


async def test_the_listing_says_where_each_game_came_from(db_session: AsyncSession) -> None:
    """El front necesita el origen para explicar los huecos: una partida
    importada de un PGN no trae ratings ni ritmo, y cuatro columnas vacías sin
    una palabra se leen como un fallo (fila 67 del inventario de
    docs/07-coherencia-ui.md)."""
    await _create_game(db_session, platform_id="s1", white="ana", black="beto")
    await _create_game(db_session, platform_id="m1", white="ana", black="caro", platform="manual")
    await _create_game(db_session, platform_id="b1", white="ana", black="dani", platform="board")
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/games")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    platforms = {game["black_username"]: game["platform"] for game in response.json()}
    assert platforms == {"beto": "chesscom", "caro": "manual", "dani": "board"}

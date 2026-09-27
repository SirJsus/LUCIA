"""Importación de PGN manual (RF-1.5): el servicio y el endpoint."""

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Game, Player
from lucia_api.main import app
from lucia_api.services.pgn_import import import_pgn
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

OTB_PGN = """[Event "Torneo Interclubes"]
[Site "Monterrey MEX"]
[Date "2026.03.14"]
[White "Duran, Jesus"]
[Black "Gomez, Ana"]
[Result "1-0"]
[WhiteElo "1832"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 1-0
"""

LICHESS_PGN = """[Event "Rated blitz game"]
[UTCDate "2026.05.02"]
[UTCTime "18:30:00"]
[White "rival_anonimo"]
[Black "jesus_otb"]
[Result "1/2-1/2"]
[TimeControl "300+3"]

1. d4 d5 2. c4 e6 1/2-1/2
"""

UNFINISHED_PGN = """[White "Uno"]
[Black "Otro"]
[Result "*"]

1. e4 *
"""


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_import_attributes_the_player_side_to_the_username(db_session: AsyncSession) -> None:
    summary = await import_pgn(
        db_session, OTB_PGN, username="sirjsus", player_name_in_pgn="Duran, Jesus"
    )

    assert summary.games_imported == 1
    game = (await db_session.execute(select(Game))).scalar_one()
    # El bando del usuario se guarda con su usuario de LUCIA, para que la
    # partida cuente en el dashboard; el rival, tal como lo nombra el PGN.
    assert game.white_username == "sirjsus"
    assert game.black_username == "Gomez, Ana"
    assert game.pgn.count("Duran, Jesus") == 1  # el nombre original sigue en el PGN


async def test_import_fills_what_the_pgn_does_not_bring(db_session: AsyncSession) -> None:
    await import_pgn(db_session, OTB_PGN, username="sirjsus", player_name_in_pgn="Duran, Jesus")

    game = (await db_session.execute(select(Game))).scalar_one()
    assert game.white_rating == 1832  # sí venía en el archivo
    assert game.black_rating == 0  # no venía: hueco, no dato inventado
    assert game.time_class == "unknown"
    assert game.time_control == "-"
    assert game.rated is False
    assert game.played_at.year == 2026 and game.played_at.month == 3
    assert (game.year, game.month) == (2026, 3)
    # La apertura se deduce igual que en las partidas de chess.com (RF-3.2).
    assert game.opening_name and "Italian" in game.opening_name


async def test_import_reads_utc_headers_and_draws(db_session: AsyncSession) -> None:
    await import_pgn(db_session, LICHESS_PGN, username="jesus_otb", player_name_in_pgn="jesus_otb")

    game = (await db_session.execute(select(Game))).scalar_one()
    assert (game.white_result, game.black_result) == ("draw", "draw")
    assert game.played_at.hour == 18
    assert game.time_control == "300+3"


async def test_reimporting_the_same_file_does_not_duplicate(db_session: AsyncSession) -> None:
    await import_pgn(db_session, OTB_PGN, username="sirjsus")
    summary = await import_pgn(db_session, OTB_PGN, username="sirjsus")

    assert summary.games_imported == 0
    assert summary.games_already_present == 1
    assert await db_session.scalar(select(func.count()).select_from(Game)) == 1


async def test_unfinished_games_are_skipped_with_a_reason(db_session: AsyncSession) -> None:
    summary = await import_pgn(db_session, OTB_PGN + "\n" + UNFINISHED_PGN, username="sirjsus")

    assert summary.games_imported == 1
    assert len(summary.skipped_game_reasons) == 1
    assert "Uno vs Otro" in summary.skipped_game_reasons[0]


async def test_a_name_that_matches_nobody_is_reported(db_session: AsyncSession) -> None:
    """Un `player_name_in_pgn` mal escrito guarda las partidas igual, pero no cuentan
    en ningún marcador: el resumen tiene que decirlo."""
    summary = await import_pgn(
        db_session, OTB_PGN, username="sirjsus", player_name_in_pgn="Durán, Jesús"
    )

    assert summary.games_imported == 1
    assert summary.games_matched_to_player == 0


async def test_the_player_is_recognised_when_the_pgn_already_uses_his_username(
    db_session: AsyncSession,
) -> None:
    """Un PGN de lichess ya nombra al jugador con su usuario: no hace falta
    `player_name_in_pgn`."""
    summary = await import_pgn(db_session, LICHESS_PGN, username="jesus_otb")

    assert summary.games_matched_to_player == 1


async def test_import_reuses_the_player_row_of_the_chesscom_sync(db_session: AsyncSession) -> None:
    db_session.add(Player(platform="chesscom", username="sirjsus"))
    await db_session.commit()

    await import_pgn(db_session, OTB_PGN, username="sirjsus")

    # Un jugador nuevo partiría el historial en dos.
    assert await db_session.scalar(select(func.count()).select_from(Player)) == 1


async def test_post_import_pgn_returns_the_summary(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/import/pgn",
                files={"file": ("torneo.pgn", OTB_PGN.encode(), "application/x-chess-pgn")},
                data={"username": "sirjsus", "player_name_in_pgn": "Duran, Jesus"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "games_imported": 1,
        "games_already_present": 0,
        "skipped_game_reasons": [],
        "games_matched_to_player": 1,
    }


async def test_post_import_pgn_rejects_a_file_without_games(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/import/pgn",
                files={"file": ("vacio.pgn", b"no soy un pgn", "application/x-chess-pgn")},
                data={"username": "sirjsus"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

"""Tests de estadísticas (RF-3). Lo delicado aquí es que el resultado de una
partida depende del color con el que jugó el usuario: la misma fila de `games`
es una victoria para uno y una derrota para el otro."""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.main import app
from lucia_api.services.stats import get_player_stats
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "a"]\n[Black "b"]\n[Result "1-0"]\n\n1. e4 e5 1-0\n'


async def _add_game(
    session: AsyncSession,
    *,
    platform_id: str,
    white: str,
    black: str,
    white_result: str,
    black_result: str,
    time_class: str = "blitz",
    white_rating: int = 1500,
    black_rating: int = 1500,
    eco: str | None = None,
    year: int = 2024,
    month: int = 1,
    days_ago: int = 0,
) -> Game:
    player = Player(platform="chesscom", username=f"dummy-{platform_id}")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id=platform_id,
        pgn=PGN,
        white_username=white,
        white_rating=white_rating,
        white_result=white_result,
        black_username=black,
        black_rating=black_rating,
        black_result=black_result,
        time_control="180",
        time_class=time_class,
        rules="chess",
        rated=True,
        eco=eco,
        played_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=days_ago),
        year=year,
        month=month,
    )
    session.add(game)
    await session.commit()
    return game


async def test_outcome_depends_on_the_player_color(db_session: AsyncSession) -> None:
    # Una sola partida: victoria de las blancas (ana) sobre beto.
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="checkmated",
    )

    ana_stats = await get_player_stats(db_session, "ana")
    beto_stats = await get_player_stats(db_session, "beto")

    assert (ana_stats.overall.wins, ana_stats.overall.losses) == (1, 0)
    assert (beto_stats.overall.wins, beto_stats.overall.losses) == (0, 1)


async def test_finds_the_player_regardless_of_case(db_session: AsyncSession) -> None:
    """chess.com da el perfil en minúsculas ("sirjsus") pero dentro del PGN el
    nombre va como lo escribió el jugador ("SirJsus"). Buscar por el nombre del
    perfil tiene que encontrar sus partidas igualmente."""
    await _add_game(
        db_session,
        platform_id="g1",
        white="SirJsus",
        black="Rival",
        white_result="win",
        black_result="resigned",
    )

    stats = await get_player_stats(db_session, "sirjsus")

    assert stats.total_games == 1
    assert stats.overall.wins == 1


async def test_counts_draws_separately(db_session: AsyncSession) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="agreed",
        black_result="agreed",
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="ana",
        black="beto",
        white_result="stalemate",
        black_result="stalemate",
    )

    stats = await get_player_stats(db_session, "ana")

    assert stats.overall.draws == 2
    assert stats.overall.wins == 0
    assert stats.overall.score_percent == 50.0


async def test_groups_by_time_class_with_the_most_recent_rating(
    db_session: AsyncSession,
) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
        time_class="bullet",
        white_rating=1400,
        days_ago=10,
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
        time_class="bullet",
        white_rating=1450,
        days_ago=1,  # más reciente: este rating es el que debe reportarse
    )
    await _add_game(
        db_session,
        platform_id="g3",
        white="beto",
        black="ana",
        white_result="win",
        black_result="resigned",
        time_class="rapid",
        black_rating=1600,
    )

    stats = await get_player_stats(db_session, "ana")
    by_time_class = {item.time_class: item for item in stats.by_time_class}

    assert by_time_class["bullet"].record.wins == 2
    assert by_time_class["bullet"].current_rating == 1450
    assert by_time_class["rapid"].record.losses == 1
    assert by_time_class["rapid"].current_rating == 1600


async def test_groups_games_by_month(db_session: AsyncSession) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="b",
        white_result="win",
        black_result="resigned",
        year=2024,
        month=1,
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="ana",
        black="b",
        white_result="win",
        black_result="resigned",
        year=2024,
        month=2,
    )
    await _add_game(
        db_session,
        platform_id="g3",
        white="ana",
        black="b",
        white_result="win",
        black_result="resigned",
        year=2024,
        month=2,
    )

    stats = await get_player_stats(db_session, "ana")

    assert [(m.year, m.month, m.games) for m in stats.by_month] == [
        (2024, 1, 1),
        (2024, 2, 2),
    ]


async def test_opening_performance_separates_colors(db_session: AsyncSession) -> None:
    italian_game_url = "https://www.chess.com/openings/Italian-Game"
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
        eco=italian_game_url,
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="beto",
        black="ana",
        white_result="win",
        black_result="resigned",
        eco=italian_game_url,
    )

    stats = await get_player_stats(db_session, "ana")
    by_color = {item.color: item for item in stats.by_opening}

    assert by_color["white"].opening == "Italian Game"  # nombre legible, no la URL
    assert by_color["white"].record.wins == 1
    assert by_color["black"].record.losses == 1


async def test_phase_stats_only_count_own_moves(
    db_session: AsyncSession,
) -> None:
    game = await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
    )
    analysis = Analysis(
        game_id=game.id,
        engine="stockfish",
        depth=10,
        multipv=1,
        status="done",
        white_accuracy=90.0,
        black_accuracy=70.0,
    )
    db_session.add(analysis)
    await db_session.flush()

    # Una jugada de cada color en apertura; la de las negras es un blunder.
    db_session.add_all(
        [
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=0,
                color="white",
                san="e4",
                uci="e2e4",
                fen_before="x",
                classification="best",
                phase="opening",
                move_accuracy=99.0,
                win_percent_before=52.0,
                win_percent_after=52.0,
            ),
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=1,
                color="black",
                san="g5",
                uci="g7g5",
                fen_before="x",
                classification="blunder",
                phase="opening",
                move_accuracy=10.0,
                win_percent_before=48.0,
                win_percent_after=8.0,
            ),
        ]
    )
    await db_session.commit()

    ana_stats = await get_player_stats(db_session, "ana")
    beto_stats = await get_player_stats(db_session, "beto")

    ana_opening_phase = next(p for p in ana_stats.by_phase if p.phase == "opening")
    beto_opening_phase = next(p for p in beto_stats.by_phase if p.phase == "opening")

    assert ana_opening_phase.moves == 1
    assert ana_opening_phase.blunders == 0
    assert ana_opening_phase.average_accuracy == 99.0

    assert beto_opening_phase.moves == 1
    assert beto_opening_phase.blunders == 1
    assert beto_opening_phase.average_win_percent_lost == 40.0

    # La precisión global también sale del bando correcto.
    assert ana_stats.average_accuracy == 90.0
    assert beto_stats.average_accuracy == 70.0
    assert ana_stats.analyzed_games == 1


async def test_stats_endpoint_returns_the_summary(db_session: AsyncSession) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
    )

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.get("/stats", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "ana"
    assert body["overall"]["wins"] == 1
    assert body["overall"]["total"] == 1


async def test_stats_endpoint_without_username_or_config_returns_422(
    db_session: AsyncSession, monkeypatch
) -> None:
    monkeypatch.setattr("lucia_api.routers.stats.settings.chesscom_username", "")

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.get("/stats")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

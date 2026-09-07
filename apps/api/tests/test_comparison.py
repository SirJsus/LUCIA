"""Comparación entre motores (RF-2.6). Lo que importa aquí es localizar las
jugadas donde Stockfish y Lc0 no opinan lo mismo, que es donde hay algo que
entender."""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.main import app
from lucia_api.services.comparison import ComparisonError, compare_analyses
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "a"]\n[Black "b"]\n[Result "1-0"]\n\n1. e4 e5 1-0\n'


async def _create_game(session: AsyncSession) -> Game:
    player = Player(platform="chesscom", username="ana")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id="g1",
        pgn=PGN,
        white_username="ana",
        white_rating=1500,
        white_result="win",
        black_username="beto",
        black_rating=1500,
        black_result="resigned",
        time_control="180",
        time_class="blitz",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2024,
        month=1,
    )
    session.add(game)
    await session.flush()
    return game


async def _create_analysis(
    session: AsyncSession,
    game_id: int,
    engine: str,
    moves: list[tuple[int, str, float, str | None, str]],
    status: str = "done",
) -> Analysis:
    """`moves` = (ply, san, win_percent_after, best_move_uci, classification)."""
    analysis = Analysis(game_id=game_id, engine=engine, depth=10, multipv=1, status=status)
    session.add(analysis)
    await session.flush()
    for ply, san, win_after, best, classification in moves:
        session.add(
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=ply,
                color="white" if ply % 2 == 0 else "black",
                san=san,
                uci="e2e4",
                fen_before="x",
                classification=classification,
                phase="opening",
                move_accuracy=90.0,
                win_percent_before=50.0,
                win_percent_after=win_after,
                best_move_uci=best,
            )
        )
    await session.commit()
    return analysis


async def test_finds_where_the_engines_disagree(db_session: AsyncSession) -> None:
    game = await _create_game(db_session)
    # Ply 0: coinciden. Ply 1: Lc0 valora la posición 30 puntos peor.
    sf = await _create_analysis(
        db_session,
        game.id,
        "stockfish",
        [(0, "e4", 52.0, "e2e4", "best"), (1, "e5", 48.0, "e7e5", "best")],
    )
    lc0 = await _create_analysis(
        db_session,
        game.id,
        "lc0",
        [(0, "e4", 51.0, "e2e4", "best"), (1, "e5", 18.0, "c7c5", "inaccuracy")],
    )

    comparison = await compare_analyses(db_session, sf.id, lc0.id)

    assert comparison.total_moves == 2
    assert comparison.agreed_best_moves == 1  # solo coinciden en el ply 0
    assert comparison.best_move_agreement_percent == 50.0
    assert len(comparison.disagreements) == 1

    disagreement = comparison.disagreements[0]
    assert disagreement.ply == 1
    assert disagreement.win_percent_gap == 30.0
    assert disagreement.same_best_move is False
    assert disagreement.classification_a == "best"
    assert disagreement.classification_b == "inaccuracy"


async def test_small_differences_do_not_count_as_disagreement(
    db_session: AsyncSession,
) -> None:
    """Dos motores nunca dan el mismo número exacto; sin umbral, todas las
    jugadas saldrían como discrepancia."""
    game = await _create_game(db_session)
    sf = await _create_analysis(db_session, game.id, "stockfish", [(0, "e4", 52.0, "e2e4", "best")])
    lc0 = await _create_analysis(db_session, game.id, "lc0", [(0, "e4", 55.0, "e2e4", "best")])

    comparison = await compare_analyses(db_session, sf.id, lc0.id)

    assert comparison.disagreements == []
    assert comparison.agreed_best_moves == 1


async def test_the_threshold_is_adjustable(db_session: AsyncSession) -> None:
    game = await _create_game(db_session)
    sf = await _create_analysis(db_session, game.id, "stockfish", [(0, "e4", 52.0, "e2e4", "best")])
    lc0 = await _create_analysis(db_session, game.id, "lc0", [(0, "e4", 55.0, "e2e4", "best")])

    strict_comparison = await compare_analyses(db_session, sf.id, lc0.id, threshold=1.0)

    assert len(strict_comparison.disagreements) == 1


async def test_disagreements_are_sorted_from_largest_to_smallest(db_session: AsyncSession) -> None:
    game = await _create_game(db_session)
    sf = await _create_analysis(
        db_session,
        game.id,
        "stockfish",
        [(0, "e4", 50.0, "e2e4", "best"), (1, "e5", 50.0, "e7e5", "best")],
    )
    lc0 = await _create_analysis(
        db_session,
        game.id,
        "lc0",
        [(0, "e4", 65.0, "d2d4", "good"), (1, "e5", 10.0, "c7c5", "blunder")],
    )

    comparison = await compare_analyses(db_session, sf.id, lc0.id)

    assert [d.win_percent_gap for d in comparison.disagreements] == [40.0, 15.0]


async def test_only_compares_the_plies_present_in_both(db_session: AsyncSession) -> None:
    """Si un análisis se cortó a medias, la parte que falta no se compara."""
    game = await _create_game(db_session)
    sf = await _create_analysis(
        db_session,
        game.id,
        "stockfish",
        [(0, "e4", 50.0, "e2e4", "best"), (1, "e5", 50.0, "e7e5", "best")],
    )
    lc0 = await _create_analysis(db_session, game.id, "lc0", [(0, "e4", 50.0, "e2e4", "best")])

    comparison = await compare_analyses(db_session, sf.id, lc0.id)

    assert comparison.total_moves == 1


async def test_rejects_comparing_analyses_of_different_games(
    db_session: AsyncSession,
) -> None:
    game1 = await _create_game(db_session)
    player2 = Player(platform="chesscom", username="otro")
    db_session.add(player2)
    await db_session.flush()
    game2 = Game(
        player_id=player2.id,
        platform="chesscom",
        platform_id="g2",
        pgn=PGN,
        white_username="x",
        white_rating=1,
        white_result="win",
        black_username="y",
        black_rating=1,
        black_result="resigned",
        time_control="180",
        time_class="blitz",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2024,
        month=1,
    )
    db_session.add(game2)
    await db_session.flush()

    a = await _create_analysis(db_session, game1.id, "stockfish", [])
    b = await _create_analysis(db_session, game2.id, "lc0", [])

    with pytest.raises(ComparisonError, match="partidas distintas"):
        await compare_analyses(db_session, a.id, b.id)


async def test_rejects_comparing_if_either_one_is_unfinished(db_session: AsyncSession) -> None:
    game = await _create_game(db_session)
    a = await _create_analysis(db_session, game.id, "stockfish", [])
    b = await _create_analysis(db_session, game.id, "lc0", [], status="running")

    with pytest.raises(ComparisonError, match="terminados"):
        await compare_analyses(db_session, a.id, b.id)


async def test_comparison_endpoint(db_session: AsyncSession) -> None:
    game = await _create_game(db_session)
    sf = await _create_analysis(db_session, game.id, "stockfish", [(0, "e4", 52.0, "e2e4", "best")])
    lc0 = await _create_analysis(db_session, game.id, "lc0", [(0, "e4", 20.0, "d2d4", "mistake")])

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.get(
                "/analysis/compare", params={"analysis_a": sf.id, "analysis_b": lc0.id}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["engine_a"] == "stockfish"
    assert body["engine_b"] == "lc0"
    assert len(body["disagreements"]) == 1
    assert body["disagreements"][0]["win_percent_gap"] == 32.0


async def test_compare_is_not_mistaken_for_an_analysis_id(
    db_session: AsyncSession,
) -> None:
    """`/analysis/compare` se declara antes que `/analysis/{analysis_id}`."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.get("/analysis/compare", params={"analysis_a": 999, "analysis_b": 998})
    finally:
        app.dependency_overrides.clear()

    # 422 del servicio (no existen), no un error de tipo de ruta.
    assert response.status_code == 422
    assert "no existe" in response.json()["detail"]

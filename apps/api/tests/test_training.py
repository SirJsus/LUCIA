"""Tests del entrenamiento desde los errores propios (RF-4.1 con RF-10.3).

Lo delicado aquí es de qué jugadas sale un puzzle y qué respuestas se le dan
por buenas; el algoritmo de repetición espaciada en sí se prueba aparte, sobre
`lucia_core.training`, porque ahí es puro.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

import chess
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player, Puzzle
from lucia_api.main import app
from lucia_api.services.review import review_queue
from lucia_api.services.training import answer_puzzle, generate_puzzles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "ana"]\n[Black "beto"]\n[Result "0-1"]\n\n1. a3 e5 0-1\n'

#: Tres líneas del motor sobre la posición inicial: las dos primeras valen casi
#: lo mismo (unos 1,8 puntos de probabilidad de victoria) y la tercera pierde
#: nueve. Es el material con el que se comprueba RF-10.3.
ALTERNATIVES = [
    {"score_cp": 100, "score_mate": None, "pv": ["e2e4", "e7e5"]},
    {"score_cp": 80, "score_mate": None, "pv": ["d2d4", "d7d5"]},
    {"score_cp": 0, "score_mate": None, "pv": ["a2a3", "e7e5"]},
]


async def _add_analyzed_game(
    session: AsyncSession,
    *,
    platform_id: str = "g1",
    white: str = "ana",
    black: str = "beto",
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
        white_rating=1500,
        white_result="resigned",
        black_username=black,
        black_rating=1500,
        black_result="win",
        time_control="180",
        time_class="blitz",
        rules="chess",
        rated=True,
        played_at=dt.datetime(2026, 1, 1, tzinfo=dt.UTC),
        year=2026,
        month=1,
    )
    session.add(game)
    await session.flush()
    session.add(Analysis(game_id=game.id, engine="stockfish", depth=18, multipv=3, status="done"))
    await session.commit()
    return game


async def _add_move(
    session: AsyncSession,
    game: Game,
    *,
    ply: int = 0,
    color: str = "white",
    san: str = "a3",
    uci: str = "a2a3",
    fen_before: str = chess.STARTING_FEN,
    classification: str = "blunder",
    alternatives: list[dict] | None = None,
    best_move_uci: str | None = "e2e4",
) -> AnalyzedMove:
    analysis = (
        await session.execute(select(Analysis).where(Analysis.game_id == game.id))
    ).scalar_one()
    move = AnalyzedMove(
        analysis_id=analysis.id,
        ply=ply,
        color=color,
        san=san,
        uci=uci,
        fen_before=fen_before,
        classification=classification,
        phase="opening",
        move_accuracy=20.0,
        win_percent_before=59.1,
        win_percent_after=30.0,
        best_move_uci=best_move_uci,
        alternatives_json=ALTERNATIVES if alternatives is None else alternatives,
    )
    session.add(move)
    await session.commit()
    return move


async def test_generates_a_puzzle_from_an_own_blunder(db_session: AsyncSession) -> None:
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game)

    assert await generate_puzzles(db_session, "ana") == 1

    puzzle = (await db_session.execute(select(Puzzle))).scalar_one()
    assert puzzle.fen == chess.STARTING_FEN
    assert puzzle.played_uci == "a2a3"
    assert puzzle.interval_days == 0  # toca ya


async def test_the_rivals_blunders_are_not_my_puzzles(db_session: AsyncSession) -> None:
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game, color="black", ply=1, san="e5", uci="e7e5")

    assert await generate_puzzles(db_session, "ana") == 0


async def test_inaccuracies_do_not_become_puzzles(db_session: AsyncSession) -> None:
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game, classification="inaccuracy")

    assert await generate_puzzles(db_session, "ana") == 0


async def test_equivalent_moves_are_accepted_as_solutions(db_session: AsyncSession) -> None:
    """RF-10.3: las dos líneas que valen casi lo mismo son las dos buenas, y
    la que pierde nueve puntos no."""
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game)

    await generate_puzzles(db_session, "ana")

    puzzle = (await db_session.execute(select(Puzzle))).scalar_one()
    assert puzzle.solutions_json == ["e2e4", "d2d4"]


async def test_without_alternatives_the_only_solution_is_the_engine_move(
    db_session: AsyncSession,
) -> None:
    """Un análisis anterior a RF-10.1 cuyas posiciones ya no están en la caché
    solo tiene `best_move_uci`: da puzzle, con una sola respuesta buena."""
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game, alternatives=[])

    await generate_puzzles(db_session, "ana")

    puzzle = (await db_session.execute(select(Puzzle))).scalar_one()
    assert puzzle.solutions_json == ["e2e4"]


async def test_a_mistake_with_no_engine_move_at_all_gives_no_puzzle(
    db_session: AsyncSession,
) -> None:
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game, alternatives=[], best_move_uci=None)

    assert await generate_puzzles(db_session, "ana") == 0


async def test_generating_twice_neither_duplicates_nor_resets_the_review(
    db_session: AsyncSession,
) -> None:
    game = await _add_analyzed_game(db_session)
    await _add_move(db_session, game)
    await generate_puzzles(db_session, "ana")
    puzzle = (await db_session.execute(select(Puzzle))).scalar_one()
    await answer_puzzle(db_session, puzzle, "e2e4", attempt_number=1, now=_NOW)

    assert await generate_puzzles(db_session, "ana") == 0

    puzzles = (await db_session.execute(select(Puzzle))).scalars().all()
    assert len(puzzles) == 1
    assert puzzles[0].repetitions == 1  # el repaso hecho sigue ahí


_NOW = dt.datetime(2026, 9, 19, 12, 0, tzinfo=dt.UTC)


async def _one_puzzle(session: AsyncSession) -> Puzzle:
    game = await _add_analyzed_game(session)
    await _add_move(session, game)
    await generate_puzzles(session, "ana")
    return (await session.execute(select(Puzzle))).scalar_one()


async def test_answering_right_at_the_first_try_schedules_it_for_tomorrow(
    db_session: AsyncSession,
) -> None:
    puzzle = await _one_puzzle(db_session)

    answer = await answer_puzzle(db_session, puzzle, "e2e4", attempt_number=1, now=_NOW)

    assert answer.correct and answer.reviewed
    assert answer.solutions_san == ["e4", "d4"]  # en algebraica, derivadas del FEN
    assert answer.played_san == "a3"
    assert puzzle.interval_days == 1
    assert puzzle.due_at == _NOW + dt.timedelta(days=1)


async def test_an_equivalent_answer_counts_as_right(db_session: AsyncSession) -> None:
    puzzle = await _one_puzzle(db_session)

    answer = await answer_puzzle(db_session, puzzle, "d2d4", attempt_number=1, now=_NOW)

    assert answer.correct


async def test_a_wrong_answer_leaves_the_puzzle_open_and_hides_the_solution(
    db_session: AsyncSession,
) -> None:
    puzzle = await _one_puzzle(db_session)

    answer = await answer_puzzle(db_session, puzzle, "h2h4", attempt_number=1, now=_NOW)

    assert not answer.correct and not answer.reviewed
    assert answer.solutions_san == [] and answer.played_san is None
    assert puzzle.last_reviewed_at is None  # no se anota nada hasta cerrarlo


async def test_giving_up_closes_it_as_failed(db_session: AsyncSession) -> None:
    puzzle = await _one_puzzle(db_session)

    answer = await answer_puzzle(db_session, puzzle, None, attempt_number=2, now=_NOW)

    assert not answer.correct and answer.reviewed
    assert answer.solutions_san == ["e4", "d4"]
    assert puzzle.repetitions == 0
    assert puzzle.ease_factor < 2.5


async def test_the_queue_only_brings_what_is_due(db_session: AsyncSession) -> None:
    puzzle = await _one_puzzle(db_session)
    await answer_puzzle(db_session, puzzle, "e2e4", attempt_number=1, now=_NOW)

    queue = await review_queue(db_session, Puzzle, _NOW, limit=10)

    assert queue.items == [] and queue.due == 0 and queue.total == 1
    assert queue.next_due_at == _NOW + dt.timedelta(days=1)


def _override_session(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_the_queue_endpoint_never_reveals_the_solution(
    db_session: AsyncSession,
) -> None:
    await _one_puzzle(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/training/puzzles")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["due"] == 1
    served = body["puzzles"][0]
    assert served["opponent"] == "beto"
    assert served["player_color"] == "white"
    assert "solutions_json" not in served and "played_uci" not in served


async def test_the_answer_endpoint_reports_the_next_review(db_session: AsyncSession) -> None:
    puzzle = await _one_puzzle(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                f"/training/puzzles/{puzzle.id}/answer", json={"uci": "e2e4", "attempt_number": 1}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["correct"] and body["reviewed"]
    assert body["solutions_san"] == ["e4", "d4"]
    assert body["classification"] == "blunder"
    assert body["interval_days"] == 1


async def test_an_open_puzzle_never_travels_with_what_would_solve_it(
    db_session: AsyncSession,
) -> None:
    """Una respuesta equivocada deja el puzzle abierto, y entonces la
    respuesta HTTP no puede llevar nada que lo resuelva: ni la solución, ni la
    jugada de la partida, ni lo que costó aquel error."""
    puzzle = await _one_puzzle(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                f"/training/puzzles/{puzzle.id}/answer", json={"uci": "h2h4", "attempt_number": 1}
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert not body["correct"] and not body["reviewed"]
    assert body["solutions_san"] == []
    assert body["played_san"] is None
    assert body["classification"] is None
    assert body["win_percent_before"] is None and body["win_percent_after"] is None
    assert body["due_at"] is None and body["interval_days"] is None


async def test_answering_a_puzzle_that_does_not_exist_is_a_404(db_session: AsyncSession) -> None:
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/training/puzzles/999/answer", json={"uci": "e2e4"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

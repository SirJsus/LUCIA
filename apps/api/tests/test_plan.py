"""Tests del plan de entrenamiento semanal (RF-4.5).

Lo delicado aquí no son las reglas —esas son puras y se prueban en
`packages/core/tests/test_plan.py`— sino **la traducción**: que las cinco
formas de contar de RF-3 lleguen al núcleo como los cinco números que espera,
y que el avance salga de las fechas que la base ya guarda, sin que nadie marque
nada a mano.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

import chess
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import (
    Analysis,
    AnalyzedMove,
    Game,
    OpeningDrill,
    Player,
    Puzzle,
    SparringGame,
)
from lucia_api.main import app
from lucia_api.services.plan import weekly_training_plan
from sqlalchemy.ext.asyncio import AsyncSession

#: Un miércoles cualquiera; el lunes de su semana es el 2026-09-21.
WEDNESDAY = dt.datetime(2026, 9, 23, 12, 0, tzinfo=dt.UTC)
MONDAY = dt.datetime(2026, 9, 21, tzinfo=dt.UTC)

PGN = '[White "ana"]\n[Black "beto"]\n[Result "0-1"]\n\n1. e4 e5 2. Qh5 Nc6 0-1\n'

#: Errores por partida de prueba. Tres bastan para que la fase en la que caen
#: pase su umbral y haya debilidad que detectar.
BLUNDERS = 3


async def _add_player(session: AsyncSession) -> Player:
    player = Player(platform="chesscom", username="ana")
    session.add(player)
    await session.flush()
    return player


async def _add_analyzed_game(
    session: AsyncSession,
    player: Player,
    *,
    phase: str = "opening",
    clocks: list[int] | None = None,
) -> Game:
    """Una partida analizada con errores **posicionales** del usuario: sin
    `best_move_uci` que capture nada, `mistake_type` no los llama tácticos.

    `phase` decide qué debilidad de fase sale, y con ella qué entrenamiento
    pide el plan (RF-4.5 lo mapea en `lucia_core.plan`). `clocks` son los
    segundos restantes por media jugada, como los reporta chess.com: con
    valores bajos la partida cuenta como jugada con apuros (RF-3.5)."""
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id="g1",
        pgn=PGN,
        white_username="ana",
        white_rating=1500,
        white_result="resigned",
        black_username="beto",
        black_rating=1500,
        black_result="win",
        time_control="180",
        time_class="blitz",
        rules="chess",
        rated=True,
        clocks_json=clocks,
        played_at=dt.datetime(2026, 9, 1, tzinfo=dt.UTC),
        year=2026,
        month=9,
    )
    session.add(game)
    await session.flush()
    analysis = Analysis(
        game_id=game.id,
        engine="stockfish",
        depth=18,
        multipv=3,
        status="done",
        white_accuracy=40.0,
        black_accuracy=80.0,
    )
    session.add(analysis)
    await session.flush()
    for index in range(BLUNDERS):
        session.add(
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=index * 2,
                color="white",
                san="Qh5",
                uci="d1h5",
                fen_before=chess.STARTING_FEN,
                classification="blunder",
                phase=phase,
                move_accuracy=10.0,
                win_percent_before=60.0,
                win_percent_after=25.0,
            )
        )
    await session.commit()
    return game


async def test_losing_ground_in_the_opening_becomes_a_weakness_and_a_drill_task(
    db_session: AsyncSession,
) -> None:
    """La traducción entera de un tirón: los errores de apertura del análisis
    salen como debilidad de fase, y esa debilidad pide líneas (RF-4.2)."""
    player = await _add_player(db_session)
    await _add_analyzed_game(db_session, player)
    db_session.add(
        OpeningDrill(
            reason="opening",
            player_color="white",
            line_uci="e2e4 e7e5 g1f3",
            games=3,
            score_percent=0.0,
            repetitions=0,
            interval_days=0,
            ease_factor=2.5,
            due_at=MONDAY,
        )
    )
    await db_session.commit()

    plan = await weekly_training_plan(db_session, "ana", WEDNESDAY)

    assert plan.week_start == MONDAY
    assert plan.analyzed_games == 1
    assert ("phase", "opening") in [(w.kind, w.subject) for w in plan.weaknesses]
    drills = next(task for task in plan.tasks if task.kind == "drills")
    assert drills.weekly_target == 1  # solo hay una línea, aunque el tope semanal sea 10
    assert [reason.kind for reason in drills.reasons]


async def test_without_analysed_games_there_is_no_diagnosis(
    db_session: AsyncSession,
) -> None:
    """Y la pantalla tiene que poder distinguirlo de "no tienes problemas":
    por eso viaja `analyzed_games`."""
    await _add_player(db_session)

    plan = await weekly_training_plan(db_session, "ana", WEDNESDAY)

    assert plan.analyzed_games == 0
    assert plan.weaknesses == []
    assert plan.tasks == []


async def test_a_training_without_material_does_not_become_a_task(
    db_session: AsyncSession,
) -> None:
    """La debilidad está, pero sin líneas generadas no hay deber que poner."""
    player = await _add_player(db_session)
    await _add_analyzed_game(db_session, player)

    plan = await weekly_training_plan(db_session, "ana", WEDNESDAY)

    assert any(w.kind == "phase" for w in plan.weaknesses)
    assert [task.kind for task in plan.tasks if task.kind == "drills"] == []


async def test_progress_comes_from_what_is_already_dated_in_the_database(
    db_session: AsyncSession,
) -> None:
    """Nadie marca nada a mano: un puzzle repasado el lunes ya cuenta, y uno
    repasado la semana pasada no."""
    player = await _add_player(db_session)
    # En medio juego, que es la debilidad que pide puzzles.
    game = await _add_analyzed_game(db_session, player, phase="middlegame")
    db_session.add_all(
        [
            Puzzle(
                game_id=game.id,
                ply=ply,
                fen=chess.STARTING_FEN,
                played_uci="d1h5",
                solutions_json=["e2e4"],
                classification="blunder",
                win_percent_before=60.0,
                win_percent_after=25.0,
                due_at=MONDAY,
                last_reviewed_at=last_reviewed,
            )
            for ply, last_reviewed in [
                (0, MONDAY + dt.timedelta(hours=3)),  # esta semana
                (2, MONDAY - dt.timedelta(days=2)),  # la anterior
                (4, None),  # sin repasar
            ]
        ]
    )
    await db_session.commit()

    plan = await weekly_training_plan(db_session, "ana", WEDNESDAY)

    puzzles = next(task for task in plan.tasks if task.kind == "puzzles")
    assert puzzles.done_this_week == 1


async def test_a_replayed_position_counts_apart_from_a_plain_sparring_game(
    db_session: AsyncSession,
) -> None:
    """Las dos son partidas contra el motor y viven en la misma tabla; lo que
    las distingue es la procedencia (RF-4.4)."""
    player = await _add_player(db_session)
    # Con el reloj en dos segundos: apuros de tiempo, que es lo que pide
    # jugar partidas enteras contra el motor.
    game = await _add_analyzed_game(db_session, player, clocks=[2, 2, 2, 2, 2, 2])
    db_session.add_all(
        [
            SparringGame(
                player_color="white",
                engine="stockfish",
                engine_elo=1500,
                starting_fen=chess.STARTING_FEN,
                moves_uci_json=[],
                created_at=MONDAY + dt.timedelta(hours=1),
                updated_at=MONDAY + dt.timedelta(hours=1),
            ),
            SparringGame(
                player_color="white",
                engine="stockfish",
                engine_elo=1500,
                starting_fen=chess.STARTING_FEN,
                moves_uci_json=[],
                origin_game_id=game.id,
                origin_ply=2,
                created_at=MONDAY + dt.timedelta(hours=2),
                updated_at=MONDAY + dt.timedelta(hours=2),
            ),
        ]
    )
    await db_session.commit()

    plan = await weekly_training_plan(db_session, "ana", WEDNESDAY)

    sparring = next(task for task in plan.tasks if task.kind == "sparring")
    assert sparring.done_this_week == 1  # la que no tiene procedencia


def _override_session(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_the_endpoint_serves_each_task_with_its_reasons(
    db_session: AsyncSession,
) -> None:
    """Cada deber viaja con las debilidades que lo piden: "generado a partir de
    las debilidades detectadas" es parte de lo que se entrega."""
    player = await _add_player(db_session)
    game = await _add_analyzed_game(db_session, player)
    db_session.add(
        Puzzle(
            game_id=game.id,
            ply=0,
            fen=chess.STARTING_FEN,
            played_uci="d1h5",
            solutions_json=["e2e4"],
            classification="blunder",
            win_percent_before=60.0,
            win_percent_after=25.0,
            due_at=MONDAY,
        )
    )
    await db_session.commit()

    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/training/plan", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["analyzed_games"] == 1
    assert body["weaknesses"]
    for task in body["tasks"]:
        assert task["reasons"], f"la tarea {task['kind']} no dice por qué está"

"""Tests del drill de aperturas (RF-4.2).

Lo delicado aquí son dos cosas. Una, **de qué se genera un drill**: que las dos
barajas salgan del material que les toca, que una salida sin jugada de maestros
no genere nada y que volver a generar no duplique. Y dos, **el recorrido de la
línea**: que el rival conteste, que fallar no enseñe la respuesta y que al
cerrar se anote el repaso.

El recorrido de la línea en sí —de quién es cada jugada, cuál toca— se prueba
aparte, sobre `lucia_core.drills`, porque ahí es puro.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

import chess
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import ExplorerPositionCache, Game, OpeningDrill, Player
from lucia_api.main import app
from lucia_api.services.drills import generate_drills
from lucia_api.services.review import record_review, review_queue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

#: Una partida en la que el jugador ("ana", negras) contesta 1...b6 a 1.e4,
#: que no es teoría. Los maestros juegan 1...c5 ahí.
PGN_TEMPLATE = (
    '[White "rival"]\n[Black "ana"]\n[Result "{result}"]\n\n1. e4 b6 2. d4 Bb7 {result}\n'
)

STARTING_EPD = chess.Board().epd()


def _explorer_position(moves: list[tuple[str, str, int]]) -> dict:
    """Una respuesta del explorador con las jugadas que se le quieran poner.
    Cada una es `(uci, san, partidas)`."""
    return {
        "white": 5000,
        "draws": 3000,
        "black": 4000,
        "moves": [
            {"uci": uci, "san": san, "white": games, "draws": 0, "black": 0}
            for uci, san, games in moves
        ],
    }


async def _add_player_with_games(session: AsyncSession, results: list[str]) -> None:
    """Un jugador con tantas partidas como resultados se le pasen, todas con
    la misma apertura y la misma salida de la teoría."""
    player = Player(platform="chesscom", username="ana")
    session.add(player)
    await session.flush()
    for index, result in enumerate(results):
        session.add(
            Game(
                player_id=player.id,
                platform="chesscom",
                platform_id=f"g{index}",
                pgn=PGN_TEMPLATE.format(result=result),
                white_username="rival",
                white_rating=1500,
                white_result="win" if result == "1-0" else "resigned",
                black_username="ana",
                black_rating=1500,
                black_result="win" if result == "0-1" else "resigned",
                time_control="180",
                time_class="blitz",
                rules="chess",
                rated=True,
                opening_eco="B00",
                opening_name="Owen Defense",
                played_at=dt.datetime(2026, 1, 1, tzinfo=dt.UTC),
                year=2026,
                month=1,
            )
        )
    await session.commit()


async def _cache_theory_after_1_e4(
    session: AsyncSession, moves: list[tuple[str, str, int]]
) -> None:
    """Lo que los maestros juegan tras 1.e4, que es donde "ana" se sale."""
    board = chess.Board()
    board.push_uci("e2e4")
    session.add(ExplorerPositionCache(epd=board.epd(), masters_json=_explorer_position(moves)))
    # La posición inicial también hace falta: es la primera que se consulta,
    # y sin ella la partida se queda sin comparar antes de llegar a la salida.
    session.add(
        ExplorerPositionCache(
            epd=STARTING_EPD, masters_json=_explorer_position([("e2e4", "e4", 9000)])
        )
    )
    await session.commit()


MASTER_REPLIES = [("c7c5", "c5", 4000), ("e7e5", "e5", 3000)]


async def test_a_recurring_departure_becomes_a_drill(db_session: AsyncSession) -> None:
    """Tres derrotas saliéndose por el mismo sitio: eso es un agujero de
    repertorio, y la línea acaba en la jugada de maestros."""
    await _add_player_with_games(db_session, ["1-0", "1-0", "1-0"])
    await _cache_theory_after_1_e4(db_session, MASTER_REPLIES)

    assert (await generate_drills(db_session, "ana")).created >= 1

    drill = (await db_session.execute(select(OpeningDrill))).scalars().first()
    assert drill is not None
    assert drill.player_color == "black"
    # 1.e4 y, en lugar de 1...b6, la más jugada por los maestros.
    assert drill.line_uci == "e2e4 c7c5"
    assert drill.score_percent == 0.0


async def test_generating_twice_adds_nothing(db_session: AsyncSession) -> None:
    """La clave es (bando, línea): volver a pulsar no duplica ni toca el
    estado de repaso de lo que ya había."""
    await _add_player_with_games(db_session, ["1-0", "1-0", "1-0"])
    await _cache_theory_after_1_e4(db_session, MASTER_REPLIES)

    assert (await generate_drills(db_session, "ana")).created >= 1
    assert (await generate_drills(db_session, "ana")).created == 0


async def test_a_departure_without_a_master_move_generates_nothing(
    db_session: AsyncSession,
) -> None:
    """Sin jugada de maestros no hay nada que enseñar: un drill sin solución
    solo enseñaría a adivinar (misma regla que RF-10.3 con los puzzles)."""
    await _add_player_with_games(db_session, ["1-0", "1-0", "1-0"])
    # Ninguna llega al mínimo de partidas para contar como repertorio.
    await _cache_theory_after_1_e4(db_session, [("c7c5", "c5", 1), ("e7e5", "e5", 2)])

    assert (await generate_drills(db_session, "ana")).created == 0


async def test_a_line_played_once_is_bad_luck_and_not_a_drill(
    db_session: AsyncSession,
) -> None:
    await _add_player_with_games(db_session, ["1-0"])
    await _cache_theory_after_1_e4(db_session, MASTER_REPLIES)

    assert (await generate_drills(db_session, "ana")).created == 0


async def test_a_line_that_wins_is_not_a_drill(db_session: AsyncSession) -> None:
    """Se entrena lo que cuesta puntos, no lo que simplemente no es teoría."""
    await _add_player_with_games(db_session, ["0-1", "0-1", "0-1"])
    await _cache_theory_after_1_e4(db_session, MASTER_REPLIES)

    assert (await generate_drills(db_session, "ana")).created == 0


async def test_the_queue_serves_what_is_due(db_session: AsyncSession) -> None:
    await _add_player_with_games(db_session, ["1-0", "1-0", "1-0"])
    await _cache_theory_after_1_e4(db_session, MASTER_REPLIES)
    await generate_drills(db_session, "ana")

    queue = await review_queue(db_session, OpeningDrill, dt.datetime.now(dt.UTC), 20)
    assert queue.due == queue.total >= 1  # recién generados, tocan ya


async def test_the_queue_announces_the_next_review_in_utc(db_session: AsyncSession) -> None:
    """Terminada la tanda, «el próximo repaso toca el …» sale del primer
    vencimiento que **todavía no** ha llegado —el mínimo absoluto incluiría los
    ya vencidos— y con la zona horaria puesta: sin ella el navegador lo lee en
    su hora local y enseña el día anterior. Es el mismo trato que reciben los
    puzzles, porque la cola es una sola."""
    drill = await _one_drill(db_session)
    now = dt.datetime.now(dt.UTC)
    # Otra línea atrasada, que sigue tocando: el próximo repaso no es el suyo.
    db_session.add(
        OpeningDrill(
            source="departure",
            player_color="white",
            line_uci="d2d4 d7d5 c2c4",
            games_played=3,
            score_percent=20.0,
            due_at=now - dt.timedelta(days=2),
        )
    )
    record_review(drill, "solved", now)
    await db_session.commit()

    queue = await review_queue(db_session, OpeningDrill, now, 20)

    assert queue.due == 1  # la atrasada, que es la única que toca
    assert queue.next_due_at is not None
    assert queue.next_due_at.tzinfo is not None
    assert queue.next_due_at == now + dt.timedelta(days=1)


def _override_session(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def _one_drill(db_session: AsyncSession) -> OpeningDrill:
    await _add_player_with_games(db_session, ["1-0", "1-0", "1-0"])
    await _cache_theory_after_1_e4(db_session, MASTER_REPLIES)
    await generate_drills(db_session, "ana")
    return (await db_session.execute(select(OpeningDrill))).scalars().first()  # type: ignore[return-value]


async def test_the_queue_does_not_leak_the_line(db_session: AsyncSession) -> None:
    """La línea es la respuesta: de un drill abierto sale la posición que hay
    que jugar y nada más."""
    await _one_drill(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/training/drills", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    served = response.json()["drills"][0]
    assert "line_uci" not in served
    # Con negras, la posición ya lleva hecha la jugada del rival.
    assert served["first_player_ply"] == 1
    assert served["preceding_moves_san"] == ["e4"]
    assert served["fen"].startswith("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b")


async def test_a_wrong_move_does_not_reveal_the_right_one(db_session: AsyncSession) -> None:
    """Fallar deja volver a intentarlo, y enseñar aquí la buena convertiría el
    reintento en un trámite (misma regla que los puzzles)."""
    drill = await _one_drill(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                f"/training/drills/{drill.id}/moves",
                json={"ply": 1, "uci": "b7b6", "wrong_moves": 0},
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert body["correct"] is False
    assert body["reviewed"] is False
    assert body["line_moves_san"] == []
    assert body["next_ply"] == 1  # se vuelve a intentar la misma


async def test_finishing_the_line_closes_the_drill_and_books_the_review(
    db_session: AsyncSession,
) -> None:
    drill = await _one_drill(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                f"/training/drills/{drill.id}/moves",
                json={"ply": 1, "uci": "c7c5", "wrong_moves": 0},
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert body["correct"] is True
    assert body["reviewed"] is True
    assert body["line_moves_san"] == ["e4", "c5"]
    assert body["interval_days"] == 1  # primer acierto de SM-2
    await db_session.refresh(drill)
    assert drill.repetitions == 1


async def test_giving_up_closes_the_drill_as_failed(db_session: AsyncSession) -> None:
    drill = await _one_drill(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                f"/training/drills/{drill.id}/moves",
                json={"ply": 1, "uci": None, "wrong_moves": 2},
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert body["correct"] is False
    assert body["reviewed"] is True
    assert body["line_moves_san"] == ["e4", "c5"]
    await db_session.refresh(drill)
    assert drill.repetitions == 0  # fallar reinicia los aciertos seguidos


async def test_asking_for_a_ply_of_the_rival_is_refused(db_session: AsyncSession) -> None:
    drill = await _one_drill(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                f"/training/drills/{drill.id}/moves",
                json={"ply": 0, "uci": "e2e4", "wrong_moves": 0},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

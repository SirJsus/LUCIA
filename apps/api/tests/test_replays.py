"""Tests de "re-juega desde el error" (RF-4.4).

Son dos cosas. Una, **desde dónde se puede retomar**: que la posición salga
del PGN que ya está guardado y no de lo que mande la pantalla, que el ply
señale la posición anterior al error, y que pedir una jugada que la partida no
tiene se rechace. Y dos, **qué ofrece la lista curada**: los errores propios
más caros primero, sin los del rival.

Que la partida retomada se juegue igual que cualquier otra de sparring no se
prueba aquí: es la misma tabla y el mismo ciclo, y ya está en
`test_sparring.py`.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

import chess
import pytest
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.main import app
from lucia_api.services.replays import replay_positions
from lucia_api.services.sparring import create_game, get_game_position
from sqlalchemy.ext.asyncio import AsyncSession

from .test_sparring import FakeEngineBridge, fake_engine  # noqa: F401  (fixture)

#: "ana" lleva blancas y en la jugada 5 (ply 4) hace una barbaridad.
PGN = '[White "ana"]\n[Black "beto"]\n[Result "0-1"]\n\n1. e4 e5 2. Nf3 Nc6 3. Ng5 0-1\n'


async def _add_analyzed_game(session: AsyncSession) -> Game:
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
        white_result="resigned",
        black_username="beto",
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
    analysis = Analysis(game_id=game.id, engine="stockfish", depth=18, multipv=3, status="done")
    session.add(analysis)
    await session.flush()
    session.add_all(
        [
            # El blunder propio: 3.Cg5, en el ply 4.
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=4,
                color="white",
                san="Ng5",
                uci="f3g5",
                fen_before=chess.Board(
                    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
                ).fen(),
                classification="blunder",
                phase="opening",
                move_accuracy=20.0,
                win_percent_before=55.0,
                win_percent_after=20.0,
            ),
            # Uno del rival, que no es asunto de quien entrena.
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=3,
                color="black",
                san="Nc6",
                uci="b8c6",
                fen_before=chess.STARTING_FEN,
                classification="mistake",
                phase="opening",
                move_accuracy=40.0,
                win_percent_before=50.0,
                win_percent_after=35.0,
            ),
        ]
    )
    await session.commit()
    return game


async def test_the_position_comes_from_the_stored_pgn(db_session: AsyncSession) -> None:
    """Se manda partida y jugada, no un FEN: la posición la deriva el servidor
    de lo que ya tiene guardado."""
    game = await _add_analyzed_game(db_session)

    position = await get_game_position(db_session, game.id, 4)

    # Ply 4 = cuatro jugadas hechas = la posición **anterior** a 3.Cg5.
    assert position.fen.startswith("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w")
    assert (position.game_id, position.ply) == (game.id, 4)


async def test_the_start_of_the_game_is_ply_zero(db_session: AsyncSession) -> None:
    game = await _add_analyzed_game(db_session)
    assert (await get_game_position(db_session, game.id, 0)).fen == chess.STARTING_FEN


async def test_a_ply_the_game_never_reached_is_refused(db_session: AsyncSession) -> None:
    """Retomar desde una posición que nunca existió no es retomar nada."""
    game = await _add_analyzed_game(db_session)
    with pytest.raises(ValueError):
        await get_game_position(db_session, game.id, 40)


async def test_a_game_that_is_not_there_is_refused(db_session: AsyncSession) -> None:
    with pytest.raises(ValueError):
        await get_game_position(db_session, 9999, 0)


async def test_the_engine_opens_when_the_retaken_position_is_its_turn(
    db_session: AsyncSession,
    fake_engine: type[FakeEngineBridge],  # noqa: F811
) -> None:
    """Retomando a mitad, quien abre no es "las blancas" sino quien tenga el
    turno: aquí toca a blancas y quien entrena eligió negras."""
    game = await _add_analyzed_game(db_session)
    origin = await get_game_position(db_session, game.id, 4)

    sparring = await create_game(
        db_session,
        player_color="black",
        engine_name="stockfish",
        engine_elo=1500,
        origin=origin,
    )

    assert len(sparring.moves_uci_json) == 1
    assert sparring.starting_fen == origin.fen
    assert (sparring.origin_game_id, sparring.origin_ply) == (game.id, 4)


async def test_the_engine_waits_when_the_retaken_position_is_the_players_turn(
    db_session: AsyncSession,
    fake_engine: type[FakeEngineBridge],  # noqa: F811
) -> None:
    game = await _add_analyzed_game(db_session)
    origin = await get_game_position(db_session, game.id, 4)

    sparring = await create_game(
        db_session,
        player_color="white",
        engine_name="stockfish",
        engine_elo=1500,
        origin=origin,
    )

    assert sparring.moves_uci_json == []


async def test_the_curated_list_only_has_own_mistakes(db_session: AsyncSession) -> None:
    """El error del rival dice cómo juega el otro, no qué hay que rehacer."""
    await _add_analyzed_game(db_session)

    rows = await replay_positions(db_session, "ana", 20)

    assert [(move.san, move.color) for move, _game, _opponent in rows] == [("Ng5", "white")]
    assert rows[0].opponent == "beto"


def _override_session(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_the_endpoint_serves_what_the_error_cost(db_session: AsyncSession) -> None:
    """Aquí la evaluación sí viaja, al contrario que en un puzzle abierto: no
    hay nada que adivinar, y es lo que dice por cuál empezar."""
    await _add_analyzed_game(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/training/replays", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    served = response.json()
    assert len(served["positions"]) == 1
    assert served["positions"][0]["classification"] == "blunder"
    assert served["positions"][0]["win_percent_before"] == 55.0
    assert served["positions"][0]["ply"] == 4


async def test_the_endpoint_says_how_many_mistakes_there_are_in_total(
    db_session: AsyncSession,
) -> None:
    """El total no es el largo de la lista: viene recortada a `limit`, y sin él
    la pantalla enseña veinte de trescientos sin decir que hay más (fila 102
    del inventario de docs/07-coherencia-ui.md)."""
    await _add_analyzed_game(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/training/replays", params={"username": "ana", "limit": 1})
    finally:
        app.dependency_overrides.clear()

    served = response.json()
    assert len(served["positions"]) == 1
    assert served["total"] == 1


async def test_retaking_from_an_impossible_ply_is_refused_by_the_endpoint(
    db_session: AsyncSession,
    fake_engine: type[FakeEngineBridge],  # noqa: F811
) -> None:
    game = await _add_analyzed_game(db_session)
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/sparring/games",
                json={
                    "player_color": "white",
                    "engine": "stockfish",
                    "engine_elo": 1500,
                    "origin": {"game_id": game.id, "ply": 40},
                },
                params={"username": "ana"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def test_a_resumed_game_says_from_which_ply_it_starts(
    db_session: AsyncSession,
    fake_engine: type[FakeEngineBridge],  # noqa: F811
) -> None:
    """`starting_ply` sale de la posición retomada y no de `origin_ply`.

    Son dos números distintos en cuanto la partida de origen no empieza en la
    salida: `origin_ply` cuenta desde el inicio de esa partida y `starting_ply`
    es la jugada real del tablero. Con él la lista de jugadas de la partida de
    sparring numera desde donde se retomó, en vez de desde 1 dos centímetros
    debajo del panel que lo dice (fila 101 del inventario de
    docs/07-coherencia-ui.md).
    """
    game = await _add_analyzed_game(db_session)
    origin = await get_game_position(db_session, game.id, 4)
    sparring = await create_game(
        db_session,
        player_color="white",
        engine_name="stockfish",
        engine_elo=1500,
        origin=origin,
    )

    _override_session(db_session)
    try:
        with TestClient(app) as http:
            served = http.get(f"/sparring/games/{sparring.id}", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    assert served.status_code == 200
    # La partida de origen empieza en la salida, así que aquí los dos coinciden
    # en 4; lo que se fija es de dónde sale cada uno.
    assert served.json()["starting_ply"] == 4
    assert served.json()["origin_ply"] == 4

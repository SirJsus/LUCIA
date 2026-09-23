"""Tests del sparring contra el motor (RF-4.3).

Lo delicado aquí es el turno: que el motor abra cuando le toca, que conteste
en la misma petición en la que se juega, que no se pueda mover fuera de turno
ni sobre una partida terminada, y que el final quede escrito en la fila. Las
reglas puras —rehacer la partida, saber si acabó, escribir el PGN— se prueban
aparte, sobre `lucia_core.sparring`.

Casi todo va con un motor de mentira: lo que se comprueba es el ciclo de la
partida, no la calidad de las jugadas. Lo que sí necesita a Stockfish de
verdad es que la fuerza calibrada se le pueda pedir sin que aborte, y eso
tiene su propio test marcado.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import chess
import pytest
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.main import app
from lucia_api.services import sparring as sparring_service
from lucia_api.services.sparring import create_game, engine_config, play_player_move, resign
from sqlalchemy.ext.asyncio import AsyncSession

from .conftest import requires_stockfish


class FakeEngineBridge:
    """Un motor que juega lo que se le diga, o la primera jugada legal.

    Sustituye a `EngineBridge` en `services.sparring`: tiene la misma forma
    —gestor de contexto asíncrono con `play`— y ninguna de sus dependencias.
    Así los tests del ciclo de la partida corren sin binarios compilados y sin
    esperar a que nadie piense.
    """

    scripted_moves: list[str] = []

    def __init__(self, config: object) -> None:
        self.config = config

    async def __aenter__(self) -> FakeEngineBridge:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def play(self, board: chess.Board) -> chess.Move:
        if FakeEngineBridge.scripted_moves:
            return chess.Move.from_uci(FakeEngineBridge.scripted_moves.pop(0))
        return next(iter(board.legal_moves))


@pytest.fixture
def fake_engine(monkeypatch: pytest.MonkeyPatch) -> type[FakeEngineBridge]:
    """El motor de mentira, en su sitio y sin jugadas dictadas. Cada test le
    escribe las suyas en `scripted_moves` si le importa cuáles sean."""
    FakeEngineBridge.scripted_moves = []
    monkeypatch.setattr(sparring_service, "EngineBridge", FakeEngineBridge)
    return FakeEngineBridge


def _override_session(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_the_engine_opens_when_it_has_white(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """Quien juega con negras tiene que encontrarse el tablero con una jugada
    hecha: si no, estaría esperando a nadie."""
    fake_engine.scripted_moves = ["e2e4"]
    game = await create_game(
        db_session, player_color="black", engine_name="stockfish", engine_elo=1500
    )
    assert game.moves_uci_json == ["e2e4"]


async def test_the_engine_waits_when_the_player_has_white(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    game = await create_game(
        db_session, player_color="white", engine_name="stockfish", engine_elo=1500
    )
    assert game.moves_uci_json == []


async def test_a_move_comes_back_with_the_engines_answer(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """Las dos jugadas en la misma petición: para quien juega es un solo turno."""
    fake_engine.scripted_moves = ["e7e5"]
    game = await create_game(
        db_session, player_color="white", engine_name="stockfish", engine_elo=1500
    )
    await play_player_move(db_session, game, "e2e4")
    assert game.moves_uci_json == ["e2e4", "e7e5"]
    assert game.result is None


async def test_an_illegal_move_is_refused(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    game = await create_game(
        db_session, player_color="white", engine_name="stockfish", engine_elo=1500
    )
    with pytest.raises(ValueError):
        await play_player_move(db_session, game, "e2e5")
    assert game.moves_uci_json == []


async def test_moving_out_of_turn_is_refused(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """El motor lleva blancas y ya abrió: mover una pieza blanca ahora sería
    jugar por el rival."""
    fake_engine.scripted_moves = ["e2e4"]
    game = await create_game(
        db_session, player_color="black", engine_name="stockfish", engine_elo=1500
    )
    with pytest.raises(ValueError):
        await play_player_move(db_session, game, "d2d4")


async def test_checkmating_the_engine_closes_the_game(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """El mate del pastor, con el motor colaborando: la partida se cierra en
    la jugada que da mate y el motor ya no contesta."""
    fake_engine.scripted_moves = ["e7e5", "b8c6", "g8f6"]
    game = await create_game(
        db_session, player_color="white", engine_name="stockfish", engine_elo=1500
    )
    for uci in ["e2e4", "d1h5", "f1c4", "h5f7"]:
        await play_player_move(db_session, game, uci)

    assert game.result == "1-0"
    assert game.termination == "checkmate"
    assert len(game.moves_uci_json) == 7  # el motor no contestó al mate


async def test_playing_on_a_finished_game_is_refused(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    game = await create_game(
        db_session, player_color="white", engine_name="stockfish", engine_elo=1500
    )
    await resign(db_session, game)
    with pytest.raises(ValueError):
        await play_player_move(db_session, game, "e2e4")


async def test_resigning_hands_the_win_to_the_engine(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    game = await create_game(
        db_session, player_color="black", engine_name="stockfish", engine_elo=1500
    )
    await resign(db_session, game)
    assert (game.result, game.termination) == ("1-0", "resignation")


async def test_lc0_games_have_no_elo(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """La fuerza de Lc0 es la de la red Maia cargada, no un número que se le
    pueda pedir: guardar uno haría creer a la pantalla que se puede elegir."""
    game = await create_game(db_session, player_color="white", engine_name="lc0", engine_elo=1500)
    assert game.engine_elo is None


def test_the_engine_config_asks_stockfish_to_hold_back() -> None:
    config = engine_config("stockfish", 1500)
    assert config.extra_options == {"UCI_LimitStrength": True, "UCI_Elo": 1500}


def test_the_engine_config_loads_maia_and_plays_a_single_node() -> None:
    """Con más de un nodo la búsqueda empieza a corregir a la red y se pierde
    justo lo que hace humana a Maia."""
    config = engine_config("lc0", None)
    assert str(config.extra_options["WeightsFile"]).endswith("maia-1500.pb.gz")
    assert (config.limit_kind, config.limit_value) == ("nodes", 1)


async def test_the_endpoint_serves_the_whole_game(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """Cada respuesta trae la partida entera: posición, jugadas y PGN, para
    que la pantalla no tenga que reconstruir nada."""
    fake_engine.scripted_moves = ["e7e5"]
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            created = http.post(
                "/sparring/games",
                json={"player_color": "white", "engine": "stockfish", "engine_elo": 1500},
                params={"username": "ana"},
            )
            played = http.post(
                f"/sparring/games/{created.json()['id']}/moves",
                json={"uci": "e2e4"},
                params={"username": "ana"},
            )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    # Una partida desde cero arranca en el ply 0, que es lo que numera su lista
    # de jugadas (fila 101 del inventario de docs/07-coherencia-ui.md); el caso
    # de la retomada a mitad está en `test_replays.py`, que es donde vive la
    # partida de origen.
    assert created.json()["starting_ply"] == 0
    body = played.json()
    assert body["moves_san"] == ["e4", "e5"]
    assert body["last_move_uci"] == "e7e5"
    assert body["is_player_turn"] is True
    assert '[White "ana"]' in body["pgn"]
    # El nombre del rival ya no viaja compuesto en la respuesta: en pantalla lo
    # arma el front con `engine` y `engine_elo` (fila 96). Aquí se comprueba
    # donde sigue viviendo, que es la cabecera del PGN.
    assert '[Black "Stockfish (1500)"]' in body["pgn"]


async def test_an_impossible_elo_is_refused_before_opening_the_engine(
    db_session: AsyncSession, fake_engine: type[FakeEngineBridge]
) -> None:
    """Un 400 de Elo aborta Stockfish a mitad; mejor un 422 antes de abrirlo."""
    _override_session(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/sparring/games",
                json={"player_color": "white", "engine": "stockfish", "engine_elo": 400},
                params={"username": "ana"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@requires_stockfish
async def test_a_calibrated_stockfish_answers_with_a_legal_move(db_session: AsyncSession) -> None:
    """Contra el binario de verdad: que `UCI_LimitStrength` y `UCI_Elo` se le
    puedan pedir sin que aborte la conexión, y que conteste jugando."""
    game = await create_game(
        db_session, player_color="white", engine_name="stockfish", engine_elo=1500
    )
    await play_player_move(db_session, game, "e2e4")

    assert len(game.moves_uci_json) == 2
    board = chess.Board()
    for uci in game.moves_uci_json:
        board.push(chess.Move.from_uci(uci))  # lanza si alguna no era legal


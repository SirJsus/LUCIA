"""Comparación del repertorio con la teoría de maestros (RF-3.6).

Lichess no se llama de verdad: el explorador se sustituye por uno falso con
teoría escrita a mano. Lo que se prueba es lo nuestro —dónde se decide que una
partida se salió del libro, qué se agrupa y qué pasa cuando falta teoría—, no
que Lichess responda.
"""

from __future__ import annotations

import datetime as dt

from lucia_api.db.models import Game, Player
from lucia_api.services.repertoire import compare_repertoire, refresh_repertoire
from lucia_lichess import ExplorerPosition
from sqlalchemy.ext.asyncio import AsyncSession

# 1. e4 e5 2. Nf3 Nc6 3. Bc4 (italiana) y luego una salida rara de las blancas.
ITALIAN_PGN = (
    '[White "ana"]\n[Black "beto"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 d6 1-0\n'
)
OFF_BOOK_PGN = '[White "ana"]\n[Black "beto"]\n[Result "0-1"]\n\n1. h3 e5 2. a3 d5 0-1\n'


class FakeExplorer:
    """Teoría de maestros de mentira, indexada por EPD.

    Solo tiene que responder a `masters(fen)`; con eso basta para probar el
    servicio sin tocar la red (RNF-10: tampoco en los tests).
    """

    def __init__(self, book: dict[str, list[tuple[str, str, int]]]) -> None:
        # book: epd -> [(uci, san, partidas)]
        self._book = book
        self.asked: list[str] = []

    async def masters(self, fen: str) -> ExplorerPosition:
        epd = " ".join(fen.split(" ")[:4])
        self.asked.append(epd)
        moves = self._book.get(epd, [])
        return ExplorerPosition.model_validate(
            {
                "white": 100 if moves else 0,
                "draws": 100 if moves else 0,
                "black": 100 if moves else 0,
                "moves": [
                    {"uci": uci, "san": san, "white": games, "draws": 0, "black": 0}
                    for uci, san, games in moves
                ],
            }
        )


def _book_after(*sans: str) -> str:
    """El EPD al que llevan esas jugadas desde la posición inicial."""
    import chess

    board = chess.Board()
    for san in sans:
        board.push_san(san)
    return board.epd()


#: Teoría mínima: e4 es libro, y tras 1. e4 e5 2. Nf3 Nc6 lo es Bb5 pero no Bc4.
BOOK = {
    _book_after(): [("e2e4", "e4", 900), ("d2d4", "d4", 800)],
    _book_after("e4", "e5"): [("g1f3", "Nf3", 700)],
    _book_after("e4", "e5", "Nf3", "Nc6"): [("f1b5", "Bb5", 600), ("d2d4", "d4", 200)],
}


async def _add_game(session: AsyncSession, *, platform_id: str, pgn: str) -> Game:
    player = Player(platform="chesscom", username=f"dummy-{platform_id}")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id=platform_id,
        pgn=pgn,
        white_username="ana",
        white_rating=1000,
        white_result="win",
        black_username="beto",
        black_rating=1000,
        black_result="resigned",
        time_control="600",
        time_class="rapid",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2026,
        month=9,
    )
    session.add(game)
    await session.commit()
    return game


async def test_without_theory_nothing_can_be_compared(db_session: AsyncSession) -> None:
    """Sin caché no se inventa una comparación: se dice cuántas posiciones
    faltan por preguntar."""
    await _add_game(db_session, platform_id="g1", pgn=ITALIAN_PGN)

    comparison = await compare_repertoire(db_session, "ana")

    assert comparison.departures == []
    assert comparison.positions_missing == 1  # la inicial, que es por donde empieza


async def test_finds_where_the_player_leaves_the_book(db_session: AsyncSession) -> None:
    """RF-3.6: la primera jugada propia que no es repertorio, con lo que
    juegan los maestros en su lugar."""
    await _add_game(db_session, platform_id="g1", pgn=ITALIAN_PGN)
    explorer = FakeExplorer(BOOK)

    await refresh_repertoire(db_session, explorer, "ana", budget=10)
    comparison = await compare_repertoire(db_session, "ana")

    assert comparison.positions_missing == 0
    assert len(comparison.departures) == 1
    departure = comparison.departures[0]
    assert departure.san == "Bc4"  # los maestros juegan Bb5 ahí
    assert departure.ply == 4  # tercera jugada de las blancas
    assert departure.master_moves == ["Bb5", "d4"]
    assert departure.games == 1
    assert departure.wins == 1
    assert departure.score_percent == 100.0


async def test_games_that_leave_the_book_at_the_same_point_are_grouped(
    db_session: AsyncSession,
) -> None:
    """Lo que interesa es el patrón: "esto lo hago ocho veces y puntúo un 25 %",
    no ocho partidas sueltas."""
    await _add_game(db_session, platform_id="g1", pgn=ITALIAN_PGN)
    await _add_game(db_session, platform_id="g2", pgn=ITALIAN_PGN.replace('"1-0"', '"0-1"'))
    explorer = FakeExplorer(BOOK)

    await refresh_repertoire(db_session, explorer, "ana", budget=10)
    comparison = await compare_repertoire(db_session, "ana")

    assert len(comparison.departures) == 1
    departure = comparison.departures[0]
    assert departure.games == 2
    assert (departure.wins, departure.losses) == (1, 1)
    assert departure.score_percent == 50.0


async def test_leaving_on_the_first_move_is_a_departure_too(db_session: AsyncSession) -> None:
    await _add_game(db_session, platform_id="g1", pgn=OFF_BOOK_PGN)
    explorer = FakeExplorer(BOOK)

    await refresh_repertoire(db_session, explorer, "ana", budget=10)
    comparison = await compare_repertoire(db_session, "ana")

    assert [departure.san for departure in comparison.departures] == ["h3"]
    assert comparison.departures[0].ply == 0


async def test_the_budget_bounds_how_much_is_asked(db_session: AsyncSession) -> None:
    """Preguntar de una en una y espaciado significa que la primera vez pueden
    faltar cientos: el tope evita dejar la petición colgada minutos."""
    await _add_game(db_session, platform_id="g1", pgn=ITALIAN_PGN)
    explorer = FakeExplorer(BOOK)

    fetched, remaining = await refresh_repertoire(db_session, explorer, "ana", budget=1)

    assert fetched == 1
    assert remaining == 1  # la siguiente posición de esa misma partida
    assert len(explorer.asked) == 1


async def test_a_position_is_asked_only_once(db_session: AsyncSession) -> None:
    """Dos partidas con la misma apertura comparten teoría: la caché es lo que
    hace que esto no crezca con el historial."""
    await _add_game(db_session, platform_id="g1", pgn=ITALIAN_PGN)
    await _add_game(db_session, platform_id="g2", pgn=ITALIAN_PGN)
    explorer = FakeExplorer(BOOK)

    await refresh_repertoire(db_session, explorer, "ana", budget=10)

    assert len(explorer.asked) == len(set(explorer.asked))

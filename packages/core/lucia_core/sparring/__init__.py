"""Partidas de sparring contra el motor (RF-4.3): cómo se rehace una, cuándo
se acabó y cómo se escribe en PGN.

Vive aquí y no en la API por lo mismo que `lucia_core.training`: son reglas de
ajedrez puras, sin base de datos, sin motor y sin reloj, así que se pueden
probar solas (RNF-8). Quien guarda la partida y quien le pide la jugada al
motor es `lucia_api.services.sparring`; quien calibra la fuerza del rival,
también, porque eso depende de qué motor esté instalado y no de las reglas.

**Aquí el servidor sí valida jugadas**, al contrario que en el tablero de
análisis, donde quien sabe de reglas es chess.js en el navegador
(`components/board/legalMoves.ts`). La diferencia es que en sparring el
servidor no guarda un documento ajeno: es el rival, tiene que contestar a la
jugada, y para contestar necesita saber que la jugada existía.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import chess
import chess.pgn

GameResult = Literal["1-0", "0-1", "1/2-1/2"]

Termination = Literal[
    "checkmate",
    "stalemate",
    "insufficient_material",
    "fifty_moves",
    "repetition",
    "resignation",
]
"""Por qué se acabó la partida. Son las causas de `chess.Termination` que se
alcanzan jugando —el resto solo salen de reglas de torneo que aquí no hay—,
más rendirse, que no es una regla del tablero sino una decisión de quien
juega y por eso python-chess no la conoce."""

_TERMINATION_BY_CHESS_REASON: dict[chess.Termination, Termination] = {
    chess.Termination.CHECKMATE: "checkmate",
    chess.Termination.STALEMATE: "stalemate",
    chess.Termination.INSUFFICIENT_MATERIAL: "insufficient_material",
    chess.Termination.FIFTY_MOVES: "fifty_moves",
    chess.Termination.SEVENTYFIVE_MOVES: "fifty_moves",
    chess.Termination.THREEFOLD_REPETITION: "repetition",
    chess.Termination.FIVEFOLD_REPETITION: "repetition",
}
"""Las tablas por repetición y por la regla de las 50 jugadas tienen cada una
dos variantes: la que puede reclamar quien juega y la que el árbitro aplica
sola (a las 75 jugadas, a la quinta repetición). Aquí se cuentan como la
misma: la partida se da por tablas en cuanto se llega, sin reclamar nada,
porque no hay a quién reclamarle."""


@dataclass(frozen=True)
class GameEnding:
    """Cómo acabó la partida: el marcador y por qué."""

    result: GameResult
    termination: Termination


def board_after_moves(starting_fen: str, moves_uci: Sequence[str]) -> chess.Board:
    """El tablero después de jugar `moves_uci` desde `starting_fen`.

    Es lo que reconstruye la partida en cada petición: de la base solo se
    guardan la posición de partida y las jugadas, que es el dato mínimo del
    que todo lo demás se deriva sin poder contradecirse.

    Lanza `ValueError` si el FEN no describe una posición legal o si alguna
    jugada no lo es en su momento —`push_uci` ya lo comprueba—. No debería
    pasar, porque las jugadas se validan al entrar, pero si pasa es mejor un
    error que una partida imposible.
    """
    board = chess.Board(starting_fen)
    for uci in moves_uci:
        board.push_uci(uci)
    return board


def moves_san(starting_fen: str, moves_uci: Sequence[str]) -> list[str]:
    """Las mismas jugadas en notación algebraica, para poder leerlas.

    El SAN no se guarda: depende de la posición en la que se juega, así que
    guardarlo sería tener la misma jugada escrita dos veces y poder
    contradecirse. Es la misma decisión que toma `AnalyzedMove`, que deriva su
    SAN de `fen_before` al servir.
    """
    board = chess.Board(starting_fen)
    return [board.san_and_push(chess.Move.from_uci(uci)) for uci in moves_uci]


def ending_of(board: chess.Board) -> GameEnding | None:
    """Cómo acabó la partida en esta posición, o `None` si sigue viva.

    Se consultan también las tablas que hay que reclamar (`claim_draw`): sin
    eso, una partida repetida tres veces seguiría "en curso" para siempre y
    el motor y quien entrena se quedarían dando vueltas.
    """
    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        return None
    return GameEnding(
        result=outcome.result(),  # type: ignore[arg-type]
        termination=_TERMINATION_BY_CHESS_REASON[outcome.termination],
    )


def resignation_ending(resigning_color: chess.Color) -> GameEnding:
    """El final de una partida que alguien abandona: gana el otro."""
    return GameEnding(
        result="0-1" if resigning_color == chess.WHITE else "1-0",
        termination="resignation",
    )


def to_pgn(
    starting_fen: str,
    moves_uci: Sequence[str],
    *,
    white: str,
    black: str,
    ending: GameEnding | None,
    date: str | None = None,
) -> str:
    """La partida en PGN, con quién la jugó y cómo acabó.

    Es lo que permite llevársela a otra parte: abrirla como tablero de
    análisis (RF-6.6) y analizarla desde ahí (RF-6.9). Una partida en curso
    también se exporta, con resultado `*`, que es como el PGN dice "esto no
    ha terminado".

    `[SetUp]` y `[FEN]` solo se escriben si la partida no arranca de la
    posición estándar, que es lo que marca una partida desde posición dada
    (hoy no pasa: el sparring empieza siempre en la inicial, y la posición
    elegida por quien juega es RF-11.1).
    """
    game = chess.pgn.Game()
    # `setup` fija la posición de partida y, si no es la estándar, escribe
    # solo `[SetUp "1"]` y `[FEN ...]`. Va antes de añadir jugadas porque es
    # lo que decide desde qué tablero se validan.
    game.setup(chess.Board(starting_fen))
    game.headers["Event"] = "Sparring en LUCIA"
    game.headers["White"] = white
    game.headers["Black"] = black
    game.headers["Result"] = ending.result if ending else "*"
    if date:
        game.headers["Date"] = date
    if ending:
        game.headers["Termination"] = ending.termination

    game.add_line(chess.Move.from_uci(uci) for uci in moves_uci)
    return game.accept(chess.pgn.StringExporter())

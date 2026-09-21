"""Las reglas de una partida de sparring, escritas como tests (RF-4.3).

Se prueban aquí, sin base de datos ni motor, porque son puras: rehacer la
partida desde sus jugadas, saber si acabó y por qué, y escribirla en PGN. Que
el motor conteste y que la partida se guarde se prueba aparte, en
`apps/api/tests/test_sparring.py`.
"""

import chess
import pytest
from lucia_core.sparring import (
    GameEnding,
    board_after_moves,
    board_at_ply,
    ending_of,
    moves_san,
    resignation_ending,
    to_pgn,
)

#: El mate del pastor, cuatro jugadas por bando. Sirve para casi todo: es una
#: partida legal, corta y terminada en jaque mate.
SCHOLARS_MATE = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]


def test_board_after_moves_rebuilds_the_position() -> None:
    board = board_after_moves(chess.STARTING_FEN, ["e2e4", "e7e5"])
    assert board.fen().startswith("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w")


def test_board_after_moves_rejects_an_illegal_move() -> None:
    """Una jugada imposible tiene que doler aquí y no dejar una partida en una
    posición que el motor no reconocería."""
    with pytest.raises(ValueError):
        board_after_moves(chess.STARTING_FEN, ["e2e4", "e7e5", "e2e4"])


def test_a_live_position_has_no_ending() -> None:
    assert ending_of(board_after_moves(chess.STARTING_FEN, ["e2e4"])) is None


def test_checkmate_ends_the_game_with_the_mating_side_winning() -> None:
    assert ending_of(board_after_moves(chess.STARTING_FEN, SCHOLARS_MATE)) == GameEnding(
        result="1-0", termination="checkmate"
    )


def test_stalemate_is_a_draw() -> None:
    stalemate = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert ending_of(stalemate) == GameEnding(result="1/2-1/2", termination="stalemate")


def test_insufficient_material_is_a_draw() -> None:
    assert ending_of(chess.Board("7k/8/6K1/8/8/8/8/8 w - - 0 1")) == GameEnding(
        result="1/2-1/2", termination="insufficient_material"
    )


def test_a_threefold_repetition_ends_the_game_without_claiming_it() -> None:
    """Nadie reclama tablas aquí: no hay árbitro a quien reclamárselas, y sin
    esto una partida repetida seguiría "viva" dando vueltas para siempre."""
    shuffle = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2
    assert ending_of(board_after_moves(chess.STARTING_FEN, shuffle)) == GameEnding(
        result="1/2-1/2", termination="repetition"
    )


def test_resigning_hands_the_win_to_the_other_side() -> None:
    assert resignation_ending(chess.WHITE) == GameEnding(result="0-1", termination="resignation")
    assert resignation_ending(chess.BLACK) == GameEnding(result="1-0", termination="resignation")


def test_moves_san_reads_the_moves_in_algebraic_notation() -> None:
    assert moves_san(chess.STARTING_FEN, SCHOLARS_MATE) == [
        "e4",
        "e5",
        "Qh5",
        "Nc6",
        "Bc4",
        "Nf6",
        "Qxf7#",
    ]


def test_pgn_carries_who_played_and_how_it_ended() -> None:
    pgn = to_pgn(
        chess.STARTING_FEN,
        SCHOLARS_MATE,
        white="ana",
        black="Stockfish (1500)",
        ending=GameEnding(result="1-0", termination="checkmate"),
        date="2026.09.21",
    )
    assert '[White "ana"]' in pgn
    assert '[Black "Stockfish (1500)"]' in pgn
    assert '[Result "1-0"]' in pgn
    assert '[Termination "checkmate"]' in pgn
    assert "1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0" in pgn


def test_an_unfinished_game_is_exported_with_an_open_result() -> None:
    """Se puede llevar al tablero de análisis a medias, y el PGN tiene una
    forma de decir "esto no ha terminado": el asterisco."""
    pgn = to_pgn(chess.STARTING_FEN, ["e2e4"], white="ana", black="Lc0 · Maia", ending=None)
    assert '[Result "*"]' in pgn
    assert "1. e4 *" in pgn


def test_a_game_from_another_position_declares_it_in_the_headers() -> None:
    """Hoy el sparring arranca siempre de la inicial, pero RF-4.4 y RF-11.1
    no: sin `[SetUp]` + `[FEN]` la partida se leería sobre otro tablero."""
    fen = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
    pgn = to_pgn(fen, ["e2e4"], white="ana", black="Lc0 · Maia", ending=None)
    assert '[SetUp "1"]' in pgn
    assert f'[FEN "{fen}"]' in pgn


def test_a_game_can_be_retaken_from_any_of_its_positions() -> None:
    """RF-4.4: `ply` cuenta jugadas ya hechas, así que el ply de un error es
    la posición **anterior** a ese error, la que hay que jugar de otra manera."""
    pgn = '[White "ana"]\n[Black "beto"]\n[Result "*"]\n\n1. e4 e5 2. Nf3 Nc6 *\n'
    assert board_at_ply(pgn, 0).fen() == chess.STARTING_FEN
    assert board_at_ply(pgn, 2).fen().startswith(
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w"
    )
    # Hasta el final de la partida, que es una posición legítima de la que
    # seguir jugando.
    assert board_at_ply(pgn, 4).fen().startswith("r1bqkbnr/pppp1ppp/2n5/4p3")


def test_retaking_a_ply_the_game_never_reached_is_refused() -> None:
    pgn = '[White "ana"]\n[Black "beto"]\n[Result "*"]\n\n1. e4 e5 *\n'
    with pytest.raises(ValueError):
        board_at_ply(pgn, 9)


def test_a_text_without_a_game_is_refused() -> None:
    with pytest.raises(ValueError):
        board_at_ply("", 0)


def test_a_text_that_is_not_a_game_has_no_position_to_retake() -> None:
    """Un texto cualquiera se lee como una partida sin jugadas, así que lo que
    lo delata es pedirle una jugada que no tiene."""
    with pytest.raises(ValueError):
        board_at_ply("esto no es un PGN", 1)

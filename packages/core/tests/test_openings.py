"""Los criterios con los que se reconoce una apertura.

La tabla es dato, no lógica: lo que se prueba aquí es cómo se recorre —qué
nombre se elige, cómo se toleran sus huecos y cuándo se da la teoría por
terminada—, que es donde están las decisiones.
"""

import chess
from lucia_core.openings import (
    MAX_UNKNOWN_PLIES_IN_A_ROW,
    default_book,
    identify_opening,
    opening_of_pgn,
)


def _moves(*sans: str) -> list[chess.Move]:
    board = chess.Board()
    for san in sans:
        board.push_san(san)
    return list(board.move_stack)


NAJDORF = _moves("e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6")


def test_the_table_is_loaded_once() -> None:
    assert len(default_book()) > 3000
    assert default_book() is default_book()  # cacheada


def test_identifies_the_most_specific_name() -> None:
    # "Siciliana: Najdorf" dice más que "Siciliana", que también encaja.
    opening = identify_opening(chess.Board(), NAJDORF).opening
    assert opening is not None
    assert opening.eco == "B90"
    assert "Najdorf" in opening.name


def test_recognizes_a_transposition() -> None:
    """Llegar a la misma posición por otro orden de jugadas es la misma
    apertura: por eso la tabla se indexa por posición y no por secuencia."""
    by_another_order = _moves("Nf3", "c5", "e4", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6")
    assert identify_opening(chess.Board(), by_another_order) == identify_opening(
        chess.Board(), NAJDORF
    )


def test_a_gap_in_the_table_does_not_end_the_theory() -> None:
    """En la Najdorf hay dos posiciones intermedias sin nombre; pararse en la
    primera dejaría la partida en "Siciliana" a secas."""
    assert identify_opening(chess.Board(), NAJDORF).book_plies == 10


def test_leaving_the_book_ends_the_search() -> None:
    """Una racha de posiciones sin nombre es haberse salido del repertorio, no
    un hueco de la tabla: la teoría termina en la última que sí lo tenía."""
    leaving_early = _moves("a3", "h6", "b3", "g5", "c3", "f6", "d3", "e6", "e3", "d6")
    game_opening = identify_opening(chess.Board(), leaving_early)
    assert game_opening.opening is not None  # "1. a3" sí tiene nombre
    assert game_opening.book_plies <= MAX_UNKNOWN_PLIES_IN_A_ROW


def test_a_game_that_does_not_start_from_the_standard_position_has_no_opening() -> None:
    """Una partida con ventaja o de Chess960 no empieza donde empieza la
    teoría, así que no se le inventa un nombre."""
    odds_board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NB1KBN1 w kq - 0 1")
    moves = [chess.Move.from_uci("g1f3")]
    assert identify_opening(odds_board, moves).opening is None


def test_opening_of_pgn_names_the_opening_from_the_moves() -> None:
    """RF-3.2: la apertura sale de las jugadas, no de lo que reporte
    chess.com, que no la trae en todas las partidas."""
    pgn = '[White "a"]\n[Black "b"]\n\n1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 *\n'
    opening = opening_of_pgn(pgn)
    assert opening is not None
    assert opening.eco == "B90"
    assert "Najdorf" in opening.name


def test_a_game_from_another_starting_position_has_no_opening() -> None:
    """Una partida con ventaja no empieza donde empieza la teoría: no se le
    inventa un nombre."""
    pgn = (
        '[White "a"]\n[Black "b"]\n[SetUp "1"]\n'
        '[FEN "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NB1KBN1 w kq - 0 1"]\n\n1. Nf3 d5 *\n'
    )
    assert opening_of_pgn(pgn) is None

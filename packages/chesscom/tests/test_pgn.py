from lucia_chesscom import parse_move_clocks

PGN_CON_RELOJES = """[Event "Live Chess"]
[Site "Chess.com"]
[White "a"]
[Black "b"]
[Result "1-0"]

1. e4 {[%clk 0:09:58.1]} 1... e5 {[%clk 0:09:57.5]} 2. Nf3 {[%clk 0:09:55.2]} 1-0
"""

PGN_SIN_RELOJES = """[Event "Correspondence"]
[White "a"]
[Black "b"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
"""


def test_extrae_relojes_en_segundos() -> None:
    assert parse_move_clocks(PGN_CON_RELOJES) == [598.1, 597.5, 595.2]


def test_pgn_sin_relojes_devuelve_none_por_jugada() -> None:
    assert parse_move_clocks(PGN_SIN_RELOJES) == [None, None, None]


def test_pgn_vacio_devuelve_lista_vacia() -> None:
    assert parse_move_clocks("") == []

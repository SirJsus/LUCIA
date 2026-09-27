from lucia_chesscom import parse_move_clocks

PGN_WITH_CLOCKS = """[Event "Live Chess"]
[Site "Chess.com"]
[White "a"]
[Black "b"]
[Result "1-0"]

1. e4 {[%clk 0:09:58.1]} 1... e5 {[%clk 0:09:57.5]} 2. Nf3 {[%clk 0:09:55.2]} 1-0
"""

PGN_WITHOUT_CLOCKS = """[Event "Correspondence"]
[White "a"]
[Black "b"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
"""


def test_extracts_clocks_in_seconds() -> None:
    assert parse_move_clocks(PGN_WITH_CLOCKS) == [598.1, 597.5, 595.2]


def test_pgn_without_clocks_returns_none_per_move() -> None:
    assert parse_move_clocks(PGN_WITHOUT_CLOCKS) == [None, None, None]


def test_empty_pgn_returns_an_empty_list() -> None:
    assert parse_move_clocks("") == []

"""Extracción de relojes por jugada desde el PGN de chess.com (RF-1.2).

Chess.com anota el tiempo restante tras cada jugada como un comentario
`{[%clk H:MM:SS.f]}` en el movetext. `python-chess` ya sabe leer esa
anotación (`chess.pgn.GameNode.clock()`); esta función solo recorre la
partida y arma la lista plana que persistencia necesita.
"""

from __future__ import annotations

import io

import chess.pgn


def parse_move_clocks(pgn_text: str) -> list[float | None]:
    """Devuelve el reloj restante (en segundos) tras cada jugada, en orden.

    `None` en la posición de una jugada que no trae anotación `%clk` (p. ej.
    partidas por correspondencia, o PGN importado de otra fuente).
    """
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return []

    clocks: list[float | None] = []
    node = game
    while node.variations:
        node = node.variations[0]
        clocks.append(node.clock())
    return clocks

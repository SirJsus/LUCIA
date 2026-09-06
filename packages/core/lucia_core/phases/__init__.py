"""Detección de fase de partida: apertura, medio juego y final (RF-3.3).

No existe una definición formal de dónde termina la apertura, así que aquí se
fija un criterio explícito, simple y comprobable, en vez de uno "inteligente"
pero imposible de explicar cuando el resultado sorprenda:

- **Final**: cuando a *ambos* bandos les queda poco material además de peones.
  Es el criterio menos discutible de los tres: con dama y poco más, la partida
  se juega distinto.
- **Apertura**: mientras el desarrollo esté a medias (quedan piezas en su
  casilla inicial) y no se haya pasado de la jugada límite. Se usan las dos
  condiciones porque cada una por su lado falla: solo por número de jugadas,
  un gambito rapidísimo seguiría "en apertura"; solo por desarrollo, una
  partida donde un alfil nunca se mueve nunca saldría de ella.
- **Medio juego**: todo lo demás.

Los umbrales son constantes con nombre, no números sueltos, para poder
ajustarlos sin releer la lógica.
"""

from __future__ import annotations

from typing import Literal

import chess

Phase = Literal["opening", "middlegame", "endgame"]

# Valor de las piezas para medir cuánto material queda (el rey no cuenta y los
# peones tampoco: lo que define un final es la ausencia de piezas, no de peones).
_PIECE_VALUES = {
    chess.QUEEN: 9,
    chess.ROOK: 5,
    chess.BISHOP: 3,
    chess.KNIGHT: 3,
}

#: Material no-peón por bando al empezar: dama + 2 torres + 2 alfiles + 2 caballos.
INITIAL_MATERIAL_PER_SIDE = 31

#: Si ambos bandos bajan de aquí, es final. 13 ≈ torre + alfil + caballo, o
#: dama + peón: material con el que el rey ya puede salir a jugar.
ENDGAME_MATERIAL_THRESHOLD = 13

#: Piezas de la fila trasera que deben haberse movido para dar por terminado
#: el desarrollo (de las 8 iniciales, sin contar el rey si solo enrocó).
DEVELOPED_PIECES_FOR_MIDDLEGAME = 4

#: Tope duro de la apertura. Aunque nadie desarrolle, a partir de aquí ya no
#: se está en apertura en ningún sentido útil.
MAX_OPENING_PLY = 24


def non_pawn_material(board: chess.Board, color: chess.Color) -> int:
    """Material de `color` sin contar peones ni rey, en puntos clásicos."""
    return sum(
        _PIECE_VALUES[piece_type] * len(board.pieces(piece_type, color))
        for piece_type in _PIECE_VALUES
    )


def detect_phase(board: chess.Board, ply: int) -> Phase:
    """Fase de una posición suelta. `ply` es el número de medias jugadas
    transcurridas (0 = posición inicial)."""
    if _is_endgame(board):
        return "endgame"
    if ply < MAX_OPENING_PLY and not _is_developed(board):
        return "opening"
    return "middlegame"


def phases_by_ply(boards: list[chess.Board]) -> list[Phase]:
    """Fase de cada posición de una partida, forzada a avanzar en un solo
    sentido.

    Posición a posición la fase puede ir y volver (basta con que se cambien
    damas y luego aparezca una promoción). Para estadísticas eso no sirve: una
    partida tiene una apertura, un medio juego y un final, en ese orden. Aquí
    se toma la fase cruda de cada posición y se impide retroceder.
    """
    orden: dict[Phase, int] = {"opening": 0, "middlegame": 1, "endgame": 2}
    resultado: list[Phase] = []
    maxima: Phase = "opening"

    for ply, board in enumerate(boards):
        actual = detect_phase(board, ply)
        if orden[actual] > orden[maxima]:
            maxima = actual
        resultado.append(maxima)
    return resultado


def _is_endgame(board: chess.Board) -> bool:
    return (
        non_pawn_material(board, chess.WHITE) <= ENDGAME_MATERIAL_THRESHOLD
        and non_pawn_material(board, chess.BLACK) <= ENDGAME_MATERIAL_THRESHOLD
    )


def _is_developed(board: chess.Board) -> bool:
    """Ambos bandos han sacado suficientes piezas de su fila trasera."""
    return all(
        _developed_pieces(board, color) >= DEVELOPED_PIECES_FOR_MIDDLEGAME
        for color in (chess.WHITE, chess.BLACK)
    )


def _developed_pieces(board: chess.Board, color: chess.Color) -> int:
    """Cuántas piezas (torres, caballos, alfiles, dama) ya no están en su
    casilla de salida. El rey se ignora: enrocar no es desarrollar, y quedarse
    en e1 tampoco significa estar en apertura."""
    back_rank = 0 if color == chess.WHITE else 7
    casillas_iniciales = {
        chess.square(file, back_rank): piece_type
        for file, piece_type in enumerate(
            [
                chess.ROOK,
                chess.KNIGHT,
                chess.BISHOP,
                chess.QUEEN,
                None,
                chess.BISHOP,
                chess.KNIGHT,
                chess.ROOK,
            ]
        )
        if piece_type is not None
    }

    movidas = 0
    for square, piece_type in casillas_iniciales.items():
        piece = board.piece_at(square)
        if piece is None or piece.piece_type != piece_type or piece.color != color:
            movidas += 1
    return movidas

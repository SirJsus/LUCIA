import chess
from lucia_core.phases import (
    INITIAL_MATERIAL_PER_SIDE,
    detect_phase,
    non_pawn_material,
    phases_by_ply,
)


def test_initial_material_is_the_expected_one() -> None:
    board = chess.Board()
    assert non_pawn_material(board, chess.WHITE) == INITIAL_MATERIAL_PER_SIDE
    assert non_pawn_material(board, chess.BLACK) == INITIAL_MATERIAL_PER_SIDE


def test_starting_position_is_opening() -> None:
    assert detect_phase(chess.Board(), ply=0) == "opening"


def test_few_pieces_is_endgame_even_early() -> None:
    # Solo reyes y peones: final por definición, sin importar el número de jugada.
    board = chess.Board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
    assert detect_phase(board, ply=4) == "endgame"


def test_full_development_moves_to_middlegame() -> None:
    # Ambos bandos con todas las piezas fuera de su fila trasera.
    board = chess.Board("r3k2r/pppppppp/2nq1n2/2b2b2/2B2B2/2NQ1N2/PPPPPPPP/R3K2R w KQkq - 0 1")
    assert detect_phase(board, ply=12) == "middlegame"


def test_max_opening_ply_leaves_the_opening() -> None:
    # Material intacto y sin desarrollar, pero muy avanzada la partida: el tope
    # de jugadas evita que siga contando como apertura.
    board = chess.Board()
    assert detect_phase(board, ply=0) == "opening"
    assert detect_phase(board, ply=40) == "middlegame"


def test_phases_do_not_go_backwards_in_a_game() -> None:
    # Se simula una secuencia cuya fase cruda oscila: final y luego una
    # posición con material otra vez. `phases_by_ply` no debe volver atrás.
    board_with_material = chess.Board()
    board_without_material = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    board_sequence = [board_with_material, board_without_material, board_with_material]

    phases = phases_by_ply(board_sequence)

    assert phases[0] == "opening"
    assert phases[1] == "endgame"
    assert phases[2] == "endgame"  # no vuelve a apertura


def test_returns_one_phase_per_position() -> None:
    boards = [chess.Board() for _ in range(5)]
    assert len(phases_by_ply(boards)) == 5

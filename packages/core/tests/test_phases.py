import chess
from lucia_core.phases import (
    INITIAL_MATERIAL_PER_SIDE,
    detect_phase,
    non_pawn_material,
    phases_by_ply,
)


def test_material_inicial_es_el_esperado() -> None:
    board = chess.Board()
    assert non_pawn_material(board, chess.WHITE) == INITIAL_MATERIAL_PER_SIDE
    assert non_pawn_material(board, chess.BLACK) == INITIAL_MATERIAL_PER_SIDE


def test_posicion_inicial_es_apertura() -> None:
    assert detect_phase(chess.Board(), ply=0) == "opening"


def test_pocas_piezas_es_final_aunque_sea_temprano() -> None:
    # Solo reyes y peones: final por definición, sin importar el número de jugada.
    board = chess.Board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
    assert detect_phase(board, ply=4) == "endgame"


def test_desarrollo_completo_pasa_a_medio_juego() -> None:
    # Ambos bandos con todas las piezas fuera de su fila trasera.
    board = chess.Board("r3k2r/pppppppp/2nq1n2/2b2b2/2B2B2/2NQ1N2/PPPPPPPP/R3K2R w KQkq - 0 1")
    assert detect_phase(board, ply=12) == "middlegame"


def test_tope_de_jugadas_saca_de_la_apertura() -> None:
    # Material intacto y sin desarrollar, pero muy avanzada la partida: el tope
    # de jugadas evita que siga contando como apertura.
    board = chess.Board()
    assert detect_phase(board, ply=0) == "opening"
    assert detect_phase(board, ply=40) == "middlegame"


def test_las_fases_no_retroceden_en_una_partida() -> None:
    # Se simula una secuencia cuya fase cruda oscila: final y luego una
    # posición con material otra vez. `phases_by_ply` no debe volver atrás.
    con_material = chess.Board()
    sin_material = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    secuencia = [con_material, sin_material, con_material]

    fases = phases_by_ply(secuencia)

    assert fases[0] == "opening"
    assert fases[1] == "endgame"
    assert fases[2] == "endgame"  # no vuelve a apertura


def test_devuelve_una_fase_por_posicion() -> None:
    boards = [chess.Board() for _ in range(5)]
    assert len(phases_by_ply(boards)) == 5

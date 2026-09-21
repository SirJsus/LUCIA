"""Las reglas del drill de aperturas, escritas como tests (RF-4.2).

Lo que se fija aquí es el recorrido de una línea: de quién es cada jugada,
cuál toca acertar, qué contesta el rival y cuándo se acabó. Y los dos umbrales
que deciden qué línea merece entrenarse, que son la lectura concreta de "las
líneas donde mi rendimiento es peor".

Se prueban sin base de datos ni red; que una salida de la teoría acabe
convertida en drill se prueba aparte, en `apps/api/tests/test_drills.py`.
"""

import chess
import pytest
from lucia_core.drills import (
    MIN_GAMES_TO_DRILL,
    DrillLine,
    is_worth_drilling,
    line_uci_from_departure,
    points_lost,
)

#: 1.e4 c5 2.Nf3 d6 — una siciliana de cuatro jugadas, que acaba en jugada de
#: negras: sirve para las dos orientaciones cambiando `player_color`.
SICILIAN = ("e2e4", "c7c5", "g1f3", "d7d6")


def white_line() -> DrillLine:
    """La misma línea recortada para que acabe en jugada de blancas."""
    return DrillLine(moves_uci=SICILIAN[:3], player_color=chess.WHITE)


def black_line() -> DrillLine:
    return DrillLine(moves_uci=SICILIAN, player_color=chess.BLACK)


def test_a_line_must_end_on_a_move_of_the_player() -> None:
    """Acabar en la del rival pediría recordar algo que no se llega a jugar."""
    with pytest.raises(ValueError):
        DrillLine(moves_uci=SICILIAN, player_color=chess.WHITE)


def test_an_empty_line_is_not_a_drill() -> None:
    with pytest.raises(ValueError):
        DrillLine(moves_uci=(), player_color=chess.WHITE)


def test_white_starts_on_the_first_ply_and_black_on_the_second() -> None:
    assert white_line().first_player_ply == 0
    assert black_line().first_player_ply == 1


def test_the_plies_alternate_from_the_players_color() -> None:
    line = black_line()
    assert [line.is_player_ply(ply) for ply in range(4)] == [False, True, False, True]


def test_the_expected_move_is_the_one_in_the_line() -> None:
    assert black_line().expected_uci_at(1) == "c7c5"
    assert white_line().expected_uci_at(2) == "g1f3"


def test_asking_for_a_move_of_the_rival_is_a_mistake() -> None:
    """Pedir la jugada del rival como si fuera propia es un error de quien
    llama, no una respuesta vacía que se propague sin avisar."""
    with pytest.raises(ValueError):
        black_line().expected_uci_at(0)


def test_the_rival_answers_until_the_line_runs_out() -> None:
    line = white_line()
    assert line.reply_uci_after(0) == "c7c5"
    assert line.reply_uci_after(2) is None  # con 2.Cf3 se acabó la línea


def test_the_board_carries_the_moves_already_played() -> None:
    assert black_line().board_at(0) == chess.Board()
    assert (
        black_line().board_at(1).fen().startswith("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b")
    )


def test_the_line_reads_in_algebraic_notation() -> None:
    assert black_line().moves_san() == ["e4", "c5", "Nf3", "d6"]


def test_a_departure_line_ends_with_the_master_move_instead_of_the_one_played() -> None:
    """La línea recorre la apertura como se jugó y termina en la decisión que
    costaba puntos, ya con la respuesta buena."""
    played = ["e2e4", "c7c5", "g1f3", "b8a6"]  # 2...Ca6, la salida
    assert line_uci_from_departure(played, departure_ply=3, book_move_uci="d7d6") == SICILIAN


def test_what_a_line_costs_counts_how_often_it_is_played() -> None:
    """El daño, no el porcentaje: una línea floja repetida quince veces cuesta
    más que una mala jugada tres, y hay que arreglarla antes."""
    assert points_lost(15, 40.0) == pytest.approx(1.5)
    assert points_lost(3, 20.0) == pytest.approx(0.9)
    assert points_lost(15, 40.0) > points_lost(3, 20.0)
    assert points_lost(4, 0.0) == pytest.approx(2.0)
    assert points_lost(4, 100.0) == pytest.approx(-2.0)


def test_only_lines_that_lose_points_often_enough_are_drilled() -> None:
    assert is_worth_drilling(MIN_GAMES_TO_DRILL, 25.0)
    # Pierde mucho, pero una vez: es mala suerte, no un agujero de repertorio.
    assert not is_worth_drilling(MIN_GAMES_TO_DRILL - 1, 0.0)
    # Se juega mucho y no cuesta nada: no hay nada que arreglar.
    assert not is_worth_drilling(20, 50.0)

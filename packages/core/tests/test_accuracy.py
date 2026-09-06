import chess
import chess.engine
from lucia_core.accuracy import game_accuracy, move_accuracy, win_percent


def test_win_percent_posicion_equilibrada_es_cercana_a_50() -> None:
    empate = win_percent(chess.engine.Cp(0))
    assert 49 <= empate <= 51


def test_win_percent_ventaja_grande_se_acerca_a_100() -> None:
    ganando = win_percent(chess.engine.Cp(900))
    assert ganando > 95


def test_win_percent_mate_a_favor_satura_cerca_de_100() -> None:
    # El modelo "lichess" reserva una probabilidad mínima para el rival
    # (nunca es *exactamente* 100/0, ni siquiera con mate forzado).
    assert win_percent(chess.engine.Mate(3)) > 99.0


def test_win_percent_mate_en_contra_satura_cerca_de_0() -> None:
    assert win_percent(chess.engine.Mate(-3)) < 1.0


def test_sin_caida_de_win_percent_precision_es_maxima() -> None:
    # La fórmula publicada de Lichess da 103.1668 - 3.1669 = 99.9999 con
    # caída cero, no 100 exacto; se acota a 100 solo si el cálculo lo supera.
    assert move_accuracy(55.0, 55.0) > 99.9


def test_mejorar_win_percent_no_supera_el_maximo() -> None:
    assert move_accuracy(50.0, 70.0) > 99.9


def test_caida_grande_da_precision_baja() -> None:
    precision = move_accuracy(90.0, 10.0)
    assert precision < 20


def test_precision_nunca_es_negativa() -> None:
    precision = move_accuracy(99.0, 0.0)
    assert precision >= 0.0


def test_game_accuracy_vacia_es_100() -> None:
    assert game_accuracy([]) == 100.0


def test_game_accuracy_partida_limpia_es_alta() -> None:
    limpia = game_accuracy([98.0, 97.0, 99.0, 96.0, 98.0, 97.5])
    assert limpia > 90


def test_game_accuracy_con_blunder_es_menor_que_sin_el() -> None:
    con_blunder = game_accuracy([98.0, 97.0, 5.0, 96.0, 98.0])
    sin_blunder = game_accuracy([98.0, 97.0, 96.0, 98.0])
    assert con_blunder < sin_blunder


def test_game_accuracy_esta_acotada_entre_0_y_100() -> None:
    valor = game_accuracy([0.0, 100.0, 0.0, 100.0, 0.0])
    assert 0.0 <= valor <= 100.0

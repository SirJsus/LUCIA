import chess
import chess.engine
from lucia_core.accuracy import game_accuracy, move_accuracy, win_percent


def test_win_percent_of_balanced_position_is_close_to_50() -> None:
    balanced_win_percent = win_percent(chess.engine.Cp(0))
    assert 49 <= balanced_win_percent <= 51


def test_win_percent_with_big_advantage_approaches_100() -> None:
    winning_win_percent = win_percent(chess.engine.Cp(900))
    assert winning_win_percent > 95


def test_win_percent_with_mate_in_favor_saturates_near_100() -> None:
    # El modelo "lichess" reserva una probabilidad mínima para el rival
    # (nunca es *exactamente* 100/0, ni siquiera con mate forzado).
    assert win_percent(chess.engine.Mate(3)) > 99.0


def test_win_percent_with_mate_against_saturates_near_0() -> None:
    assert win_percent(chess.engine.Mate(-3)) < 1.0


def test_no_win_percent_loss_gives_maximum_accuracy() -> None:
    # La fórmula publicada de Lichess da 103.1668 - 3.1669 = 99.9999 con
    # caída cero, no 100 exacto; se acota a 100 solo si el cálculo lo supera.
    assert move_accuracy(55.0, 55.0) > 99.9


def test_improving_win_percent_does_not_exceed_maximum() -> None:
    assert move_accuracy(50.0, 70.0) > 99.9


def test_big_win_percent_loss_gives_low_accuracy() -> None:
    accuracy = move_accuracy(90.0, 10.0)
    assert accuracy < 20


def test_move_accuracy_is_never_negative() -> None:
    accuracy = move_accuracy(99.0, 0.0)
    assert accuracy >= 0.0


def test_game_accuracy_of_empty_game_is_100() -> None:
    assert game_accuracy([]) == 100.0


def test_game_accuracy_of_clean_game_is_high() -> None:
    clean_game_accuracy = game_accuracy([98.0, 97.0, 99.0, 96.0, 98.0, 97.5])
    assert clean_game_accuracy > 90


def test_game_accuracy_with_blunder_is_lower_than_without() -> None:
    with_blunder = game_accuracy([98.0, 97.0, 5.0, 96.0, 98.0])
    without_blunder = game_accuracy([98.0, 97.0, 96.0, 98.0])
    assert with_blunder < without_blunder


def test_game_accuracy_is_bounded_between_0_and_100() -> None:
    bounded_accuracy = game_accuracy([0.0, 100.0, 0.0, 100.0, 0.0])
    assert 0.0 <= bounded_accuracy <= 100.0

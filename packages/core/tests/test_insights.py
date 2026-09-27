"""Los criterios de los extractores de patrones, escritos como tests.

Cada uno de estos casos es una regla del módulo: si un resultado sorprende al
usar la aplicación, aquí está la definición con la que se decidió.
"""

from lucia_core.insights import (
    InsightThresholds,
    MoveContext,
    critical_moments,
    is_time_trouble,
    mistake_type,
    mistakes_by_type,
    move_quality,
    opening_exit_win_percent,
    time_pressure,
    trend_change,
)


def _move(**overrides: object) -> MoveContext:
    """Una jugada normal y corriente: buena, en medio juego y con tiempo de
    sobra. Cada test cambia solo lo que está probando."""
    base = {
        "ply": 10,
        "color": "white",
        "san": "Nf3",
        "classification": "good",
        "phase": "middlegame",
        "accuracy": 95.0,
        "win_percent_before": 52.0,
        "win_percent_after": 51.0,
        "alternative_win_percents": (52.0, 51.0, 50.0),
        "best_alternative_san": "Nf3",
        "seconds_left": 120.0,
    }
    base.update(overrides)
    return MoveContext(**base)  # type: ignore[arg-type]


class TestCriticalMoments:
    def test_a_quiet_move_is_not_critical(self) -> None:
        assert critical_moments([_move()]) == []

    def test_only_one_move_holds_the_position(self) -> None:
        # La mejor línea saca 20 puntos a la segunda: había que encontrarla.
        moment = critical_moments([_move(alternative_win_percents=(60.0, 40.0, 38.0))])[0]
        assert moment.kinds == ("only_move",)

    def test_three_equally_good_moves_are_not_an_only_move(self) -> None:
        assert critical_moments([_move(alternative_win_percents=(60.0, 59.0, 58.0))]) == []

    def test_a_move_that_flips_the_game_is_a_swing(self) -> None:
        moment = critical_moments([_move(win_percent_before=70.0, win_percent_after=25.0)])[0]
        assert "swing" in moment.kinds

    def test_crossing_the_middle_by_a_hair_is_not_a_swing(self) -> None:
        # 51 % a 49 % cruza el 50, pero la partida no ha cambiado de manos.
        assert critical_moments([_move(win_percent_before=51.0, win_percent_after=49.0)]) == []

    def test_losing_a_won_position_without_crossing_is_not_a_swing(self) -> None:
        # De ganada a menos ganada: es ocasión perdida, no vuelco.
        moment = critical_moments([_move(win_percent_before=90.0, win_percent_after=55.0)])[0]
        assert moment.kinds == ("missed_chance",)

    def test_losing_a_won_position_is_a_missed_chance(self) -> None:
        moment = critical_moments([_move(win_percent_before=85.0, win_percent_after=55.0)])[0]
        assert "missed_chance" in moment.kinds

    def test_a_position_can_be_critical_for_several_reasons(self) -> None:
        moment = critical_moments(
            [
                _move(
                    win_percent_before=80.0,
                    win_percent_after=20.0,
                    alternative_win_percents=(80.0, 45.0),
                )
            ]
        )[0]
        assert set(moment.kinds) == {"only_move", "swing", "missed_chance"}

    def test_thresholds_are_adjustable(self) -> None:
        move = _move(alternative_win_percents=(60.0, 53.0))  # 7 puntos de diferencia
        assert critical_moments([move]) == []
        strict = InsightThresholds(only_move_gap=5.0)
        assert critical_moments([move], strict)[0].kinds == ("only_move",)


class TestMistakeType:
    def test_a_good_move_has_no_mistake_type(self) -> None:
        assert mistake_type(_move()) is None

    def test_a_blunder_with_the_clock_down_is_a_time_mistake(self) -> None:
        # Aunque hubiera una captura que ver: con 8 segundos, la causa es el reloj.
        move = _move(classification="blunder", seconds_left=8.0, best_alternative_san="Nxe5")
        assert mistake_type(move) == "time"

    def test_missing_a_capture_or_a_check_is_tactical(self) -> None:
        assert (
            mistake_type(_move(classification="mistake", best_alternative_san="Nxe5")) == "tactical"
        )
        assert (
            mistake_type(_move(classification="mistake", best_alternative_san="Qh5+")) == "tactical"
        )

    def test_an_endgame_mistake_without_a_tactic_is_an_endgame_mistake(self) -> None:
        move = _move(classification="mistake", phase="endgame", best_alternative_san="Kf2")
        assert mistake_type(move) == "endgame"

    def test_everything_else_is_positional(self) -> None:
        move = _move(classification="inaccuracy", best_alternative_san="Rd1")
        assert mistake_type(move) == "positional"

    def test_a_game_without_clocks_is_never_time_trouble(self) -> None:
        assert is_time_trouble(None) is False
        move = _move(classification="blunder", seconds_left=None, best_alternative_san="Rd1")
        assert mistake_type(move) == "positional"

    def test_counts_are_ordered_by_how_often_each_type_happens(self) -> None:
        moves = [
            _move(classification="blunder", best_alternative_san="Rd1"),
            _move(classification="mistake", best_alternative_san="Rd1"),
            _move(classification="blunder", seconds_left=5.0, best_alternative_san="Rd1"),
        ]
        counts = mistakes_by_type(moves)
        assert [count.mistake_type for count in counts] == ["positional", "time"]
        assert counts[0].mistakes == 2
        assert counts[0].blunders == 1


class TestTimePressure:
    def test_moves_are_grouped_by_how_much_clock_was_left(self) -> None:
        moves = [
            _move(seconds_left=120.0, accuracy=90.0),
            _move(seconds_left=45.0, accuracy=80.0),
            _move(seconds_left=5.0, accuracy=20.0, classification="blunder"),
        ]
        buckets = time_pressure(moves)
        assert [bucket.max_seconds_left for bucket in buckets] == [None, 60.0, 10.0]
        assert buckets[-1].blunders == 1
        assert buckets[-1].average_accuracy == 20.0

    def test_moves_without_a_clock_are_left_out(self) -> None:
        # Contarlas como "tiempo de sobra" diría algo que la partida no dice.
        assert time_pressure([_move(seconds_left=None)]) == []


class TestOpeningExit:
    def test_takes_the_evaluation_after_the_last_opening_move(self) -> None:
        moves = [
            _move(ply=0, phase="opening", win_percent_after=51.0),
            _move(ply=8, phase="opening", win_percent_after=44.0),
            _move(ply=20, phase="middlegame", win_percent_after=30.0),
        ]
        assert opening_exit_win_percent(moves) == 44.0

    def test_a_game_without_opening_moves_has_no_exit_evaluation(self) -> None:
        assert opening_exit_win_percent([_move(phase="middlegame")]) is None


class TestMoveQuality:
    def test_an_empty_period_has_no_quality(self) -> None:
        # Un mes sin jugadas analizadas no es un mes con precisión cero.
        assert move_quality([]) is None

    def test_errors_are_reported_per_hundred_moves(self) -> None:
        # Cuatro errores tácticos en doscientas jugadas son dos por cada cien.
        moves = [_move(classification="mistake", best_alternative_san="Qxf7+")] * 4
        moves += [_move()] * 196
        quality = move_quality(moves)
        assert quality is not None
        assert quality.moves == 200
        rates = {
            rate.mistake_type: rate.per_hundred_moves for rate in quality.mistakes_per_hundred_moves
        }
        assert rates["tactical"] == 2.0
        assert quality.total_mistakes_per_hundred_moves == 2.0

    def test_every_type_is_always_present_and_in_the_same_order(self) -> None:
        # La serie temporal no puede cambiar de categorías de un mes a otro.
        quality = move_quality([_move()])
        assert quality is not None
        assert [rate.mistake_type for rate in quality.mistakes_per_hundred_moves] == [
            "tactical",
            "positional",
            "time",
            "endgame",
        ]
        assert all(rate.per_hundred_moves == 0.0 for rate in quality.mistakes_per_hundred_moves)

    def test_blunders_are_counted_apart_from_the_rest(self) -> None:
        # Fallar menos y fallar menos grave son dos preguntas distintas.
        moves = [_move(classification="blunder", best_alternative_san="Rd1")]
        moves += [_move(classification="inaccuracy", best_alternative_san="Rd1")]
        moves += [_move()] * 98
        quality = move_quality(moves)
        assert quality is not None
        assert quality.blunders_per_hundred_moves == 1.0
        assert quality.total_mistakes_per_hundred_moves == 2.0


def _quality(accuracy: float, moves: int, mistakes: int = 0):
    """Un tramo con la precisión y el número de errores posicionales pedidos."""
    period_moves = [_move(classification="mistake", best_alternative_san="Rd1", accuracy=accuracy)]
    period_moves *= mistakes
    period_moves += [_move(accuracy=accuracy)] * (moves - mistakes)
    quality = move_quality(period_moves)
    assert quality is not None
    return quality


class TestTrendChange:
    def test_a_single_period_has_nothing_to_compare_against(self) -> None:
        assert trend_change([_quality(80.0, 100)]) is None

    def test_the_last_period_is_compared_against_the_previous_ones(self) -> None:
        change = trend_change([_quality(70.0, 100), _quality(70.0, 100), _quality(75.0, 100)])
        assert change is not None
        assert change.baseline_periods == 2
        assert change.accuracy_change == 5.0

    def test_only_the_last_three_periods_count_as_reference(self) -> None:
        # Comparar contra todo el historial haría que un mal año lejano
        # dijera "estás mejorando" para siempre.
        periods = [_quality(10.0, 100)] + [_quality(70.0, 100)] * 3 + [_quality(75.0, 100)]
        change = trend_change(periods)
        assert change is not None
        assert change.baseline_periods == 3
        assert change.accuracy_change == 5.0

    def test_the_reference_is_weighted_by_moves(self) -> None:
        # Un mes de dos partidas no puede pesar lo mismo que uno de cuarenta.
        change = trend_change([_quality(90.0, 10), _quality(70.0, 90), _quality(72.0, 100)])
        assert change is not None
        assert change.accuracy_change == 0.0  # la referencia es 72, no 80

    def test_more_mistakes_than_before_is_a_positive_change(self) -> None:
        # En errores, subir es empeorar: lo dice el campo, no el signo.
        change = trend_change([_quality(80.0, 100, mistakes=1), _quality(80.0, 100, mistakes=4)])
        assert change is not None
        assert change.mistake_rate_change == 3.0

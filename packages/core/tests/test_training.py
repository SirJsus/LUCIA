"""Las dos reglas del entrenamiento, escritas como tests (RF-4.1, RF-10.3).

Cada caso fija un criterio: cuándo vuelve un puzzle según cómo fue el repaso
(SM-2) y qué jugadas se aceptan como respuesta. Se prueban aquí, sin base de
datos ni motor, porque son lo que decide si entrenar sirve de algo (RNF-8);
que un error acabe convertido en puzzle se prueba aparte, en
`apps/api/tests/test_training.py`.
"""

from lucia_core.training import (
    EQUIVALENT_MOVE_MAX_WIN_PERCENT_LOSS,
    NEW_REVIEW_STATE,
    SpacedRepetitionState,
    equivalent_solutions,
    next_review,
)


def test_new_puzzle_is_due_right_away() -> None:
    assert NEW_REVIEW_STATE.interval_days == 0
    assert NEW_REVIEW_STATE.repetitions == 0


def test_first_two_hits_use_the_fixed_intervals() -> None:
    first = next_review(NEW_REVIEW_STATE, "solved")
    assert (first.repetitions, first.interval_days) == (1, 1)
    second = next_review(first, "solved")
    assert (second.repetitions, second.interval_days) == (2, 6)


def test_third_hit_onwards_multiplies_by_the_ease_factor() -> None:
    state = SpacedRepetitionState(repetitions=2, interval_days=6, ease_factor=2.5)
    third = next_review(state, "solved")
    # 6 días por la facilidad ya subida a 2,6 = 15,6, redondeado a 16.
    assert third.interval_days == 16
    assert third.repetitions == 3


def test_solving_raises_the_ease_factor_and_failing_lowers_it() -> None:
    assert next_review(NEW_REVIEW_STATE, "solved").ease_factor > NEW_REVIEW_STATE.ease_factor
    assert next_review(NEW_REVIEW_STATE, "failed").ease_factor < NEW_REVIEW_STATE.ease_factor


def test_solving_at_the_second_attempt_counts_but_costs_ease() -> None:
    # Está justo en la frontera de SM-2: cuenta como acierto y el intervalo
    # avanza, pero la facilidad baja un poco, así que el puzzle volverá antes
    # que uno resuelto a la primera.
    hesitant = next_review(NEW_REVIEW_STATE, "hesitant")
    assert hesitant.repetitions == 1
    assert hesitant.interval_days == 1
    assert (
        NEW_REVIEW_STATE.ease_factor
        > hesitant.ease_factor
        > next_review(NEW_REVIEW_STATE, "failed").ease_factor
    )


def test_failing_restarts_the_streak_but_not_the_ease_factor() -> None:
    state = SpacedRepetitionState(repetitions=4, interval_days=40, ease_factor=2.1)
    failed = next_review(state, "failed")
    assert (failed.repetitions, failed.interval_days) == (0, 1)
    assert failed.ease_factor < state.ease_factor  # se arrastra, no se reinicia a 2,5


def test_ease_factor_never_goes_below_the_floor() -> None:
    state = SpacedRepetitionState(ease_factor=1.3)
    assert next_review(state, "failed").ease_factor == 1.3


def test_a_single_line_is_the_only_solution() -> None:
    assert equivalent_solutions([("e2e4", 61.0)]) == ("e2e4",)


def test_no_lines_means_no_solution() -> None:
    assert equivalent_solutions([]) == ()


def test_lines_as_good_as_the_best_are_accepted_too() -> None:
    # Tres jugadas dentro del margen y una que pierde de más (RF-10.3).
    accepted = equivalent_solutions(
        [
            ("e2e4", 61.0),
            ("d2d4", 60.5),
            ("g1f3", 59.1),
            ("a2a3", 52.0),
        ]
    )
    assert accepted == ("e2e4", "d2d4", "g1f3")


def test_solutions_come_out_best_first_whatever_the_input_order() -> None:
    assert equivalent_solutions([("d2d4", 60.5), ("e2e4", 61.0)]) == ("e2e4", "d2d4")


def test_the_margin_is_inclusive() -> None:
    borderline = 61.0 - EQUIVALENT_MOVE_MAX_WIN_PERCENT_LOSS
    assert equivalent_solutions([("e2e4", 61.0), ("d2d4", borderline)]) == ("e2e4", "d2d4")

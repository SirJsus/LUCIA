"""Las reglas del plan de entrenamiento semanal, escritas como tests (RF-4.5).

Dos cosas se fijan aquí. Una, **qué cuenta como debilidad**: los umbrales, que
son lo que separa un problema de verdad del desgaste normal de jugar, y el
orden, que es por dónde se empieza. Y dos, **qué entrenamiento le toca a cada
una**, que es lo que hace que el plan salga "de las debilidades detectadas" y
no de una cuota inventada.

Se prueban sin base de datos ni reloj; que los números lleguen de las
estadísticas se prueba aparte, en `apps/api/tests/test_plan.py`.
"""

import datetime as dt

import pytest
from lucia_core.plan import (
    MAX_WEEKLY_TARGETS,
    MIN_ACCURACY_DROP,
    MIN_MISTAKE_TYPE_SHARE,
    MIN_OPENING_POINTS_LOST,
    MIN_PHASE_WIN_PERCENT_LOST,
    MIN_TIME_TROUBLE_SHARE,
    Weakness,
    build_weekly_tasks,
    detect_weaknesses,
    task_for_weakness,
    week_start,
)

#: Un jugador sin ningún problema detectable: todo por debajo de su umbral.
NO_WEAKNESSES = {
    "average_win_percent_lost_by_phase": {"middlegame": MIN_PHASE_WIN_PERCENT_LOST - 0.1},
    "mistake_share_by_type": {"tactical": MIN_MISTAKE_TYPE_SHARE - 0.1},
    "opening_points_lost": [("Caro-Kann Defense", "black", MIN_OPENING_POINTS_LOST - 0.1)],
    "time_trouble_share": MIN_TIME_TROUBLE_SHARE - 0.1,
    "accuracy_change": -(MIN_ACCURACY_DROP - 0.1),
}


def test_a_player_without_problems_gets_no_weaknesses() -> None:
    """Enumerar cinco debilidades siempre, las tenga o no, no ayuda a decidir
    por dónde empezar."""
    assert detect_weaknesses(**NO_WEAKNESSES) == []


def test_each_source_becomes_a_weakness_once_it_crosses_its_threshold() -> None:
    detected = detect_weaknesses(
        average_win_percent_lost_by_phase={"opening": 2.0, "middlegame": 12.0, "endgame": 4.0},
        mistake_share_by_type={"tactical": 55.0, "positional": 20.0},
        opening_points_lost=[("Caro-Kann Defense", "black", 3.0)],
        time_trouble_share=40.0,
        accuracy_change=-5.0,
    )
    assert [(w.kind, w.subject) for w in detected] == [
        ("phase", "middlegame"),
        ("mistake_type", "tactical"),
        ("opening", "Caro-Kann Defense"),
        ("time_trouble", ""),
        ("accuracy_trend", ""),
    ]


def test_an_opening_weakness_keeps_the_colour_it_hurts_with() -> None:
    """La Caro-Kann de negras y la de blancas son dos debilidades distintas, y
    el drill que sale de cada una es otro."""
    detected = detect_weaknesses(
        **{**NO_WEAKNESSES, "opening_points_lost": [("Caro-Kann Defense", "black", 3.0)]}
    )
    assert detected[0].color == "black"


def test_only_the_worst_opening_enters_the_plan() -> None:
    detected = detect_weaknesses(
        **{
            **NO_WEAKNESSES,
            "opening_points_lost": [
                ("French Defense", "black", 1.5),
                ("Caro-Kann Defense", "black", 4.0),
            ],
        }
    )
    assert [w.subject for w in detected] == ["Caro-Kann Defense"]


def test_improving_accuracy_is_not_a_weakness() -> None:
    """Subir no es empeorar: el signo importa."""
    assert detect_weaknesses(**{**NO_WEAKNESSES, "accuracy_change": 8.0}) == []


def test_an_unknown_trend_is_not_a_weakness() -> None:
    """Sin meses suficientes no hay tendencia que afirmar, y afirmarla igual
    sería inventarla."""
    assert detect_weaknesses(**{**NO_WEAKNESSES, "accuracy_change": None}) == []


@pytest.mark.parametrize(
    ("weakness", "expected"),
    [
        (Weakness(kind="phase", subject="opening", magnitude=9.0), "drills"),
        (Weakness(kind="phase", subject="middlegame", magnitude=9.0), "puzzles"),
        (Weakness(kind="phase", subject="endgame", magnitude=9.0), "replays"),
        (Weakness(kind="mistake_type", subject="tactical", magnitude=50.0), "puzzles"),
        (Weakness(kind="mistake_type", subject="positional", magnitude=50.0), "drills"),
        (Weakness(kind="mistake_type", subject="time", magnitude=50.0), "sparring"),
        (Weakness(kind="opening", subject="Caro-Kann Defense", magnitude=3.0), "drills"),
        (Weakness(kind="time_trouble", subject="", magnitude=40.0), "sparring"),
        (Weakness(kind="accuracy_trend", subject="", magnitude=5.0), "sparring"),
    ],
)
def test_every_weakness_knows_what_trains_it(weakness: Weakness, expected: str) -> None:
    assert task_for_weakness(weakness) == expected


def test_without_weaknesses_there_is_no_plan() -> None:
    """Y no es un fallo: llenar la semana igualmente sería inventarse el
    motivo."""
    assert build_weekly_tasks([], available_material={"puzzles": 50}, done_this_week={}) == []


def test_several_weaknesses_that_ask_for_the_same_training_share_one_task() -> None:
    """Fallar en el medio juego y fallar por táctica suelen ser lo mismo visto
    de dos maneras, y no dos deberes."""
    plan = build_weekly_tasks(
        [
            Weakness(kind="phase", subject="middlegame", magnitude=12.0),
            Weakness(kind="mistake_type", subject="tactical", magnitude=55.0),
        ],
        available_material={"puzzles": 50},
        done_this_week={},
    )
    assert len(plan) == 1
    assert plan[0].kind == "puzzles"
    assert [reason.kind for reason in plan[0].reasons] == ["phase", "mistake_type"]


def test_the_target_never_asks_for_more_than_there_is() -> None:
    """Pedir treinta puzzles cuando hay cuatro no es exigente, es falso."""
    plan = build_weekly_tasks(
        [Weakness(kind="mistake_type", subject="tactical", magnitude=55.0)],
        available_material={"puzzles": 4},
        done_this_week={},
    )
    assert plan[0].weekly_target == 4


def test_the_target_is_capped_by_what_fits_in_a_week() -> None:
    plan = build_weekly_tasks(
        [Weakness(kind="mistake_type", subject="tactical", magnitude=55.0)],
        available_material={"puzzles": 500},
        done_this_week={},
    )
    assert plan[0].weekly_target == MAX_WEEKLY_TARGETS["puzzles"]


def test_a_training_without_material_does_not_become_a_task() -> None:
    """Sin puzzles generados no hay deber que poner, por mucho que la
    debilidad esté ahí."""
    plan = build_weekly_tasks(
        [Weakness(kind="mistake_type", subject="tactical", magnitude=55.0)],
        available_material={"puzzles": 0},
        done_this_week={},
    )
    assert plan == []


def test_the_week_starts_on_monday_at_midnight() -> None:
    """El lunes y no "hace siete días": con una ventana móvil, lo hecho el
    lunes dejaría de contar el martes siguiente y el avance bajaría solo."""
    wednesday = dt.datetime(2026, 9, 23, 17, 30, tzinfo=dt.UTC)
    assert week_start(wednesday) == dt.datetime(2026, 9, 21, tzinfo=dt.UTC)
    monday = dt.datetime(2026, 9, 21, 0, 0, tzinfo=dt.UTC)
    assert week_start(monday) == monday
    sunday = dt.datetime(2026, 9, 27, 23, 59, tzinfo=dt.UTC)
    assert week_start(sunday) == dt.datetime(2026, 9, 21, tzinfo=dt.UTC)

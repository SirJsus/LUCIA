"""Plan de entrenamiento semanal (RF-4.5): qué falla y qué hacer esta semana.

El plan **no se guarda**: se deduce cada vez de lo que ya se sabe del jugador,
como los patrones (ADR-0008) y la lista de re-jugar (ADR-0020). No lleva
estado propio —el avance sale de lo que ya está fechado en la base: puzzles y
líneas repasados esta semana, partidas jugadas esta semana—, así que
congelarlo solo daría una copia que envejece en cuanto se analiza una partida
más.

Aquí viven las dos reglas que hacen útil al plan, puras y sin base de datos ni
reloj (RNF-8):

- **Qué cuenta como debilidad y por cuál conviene empezar**: `detect_weaknesses`.
- **Qué entrenamiento le toca a cada una, y cuánto**: `build_weekly_tasks`.

Quien carga el material —las estadísticas de RF-3 y las colas de RF-4— es
`lucia_api.services.plan`. Aquí solo llegan números.

**Por qué un plan y no una lista de deberes.** El requerimiento dice "generado
a partir de las debilidades detectadas", así que cada tarea nace de una
debilidad concreta y la lleva encima: sin eso sería una cuota semanal
arbitraria, y quien entrena no podría discutirla ni entender por qué cambia.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

WeaknessKind = Literal["phase", "mistake_type", "opening", "time_trouble", "accuracy_trend"]
"""Qué clase de problema se ha detectado. Cada uno sale de un requerimiento de
RF-3 distinto y apunta a un entrenamiento distinto."""

TrainingTaskKind = Literal["puzzles", "drills", "replays", "sparring"]
"""Qué hacer al respecto, en las cuatro formas de entrenar que existen:
puzzles (RF-4.1), líneas de apertura (RF-4.2), re-jugar posiciones (RF-4.4) y
partidas contra el motor (RF-4.3)."""

#: Cuánta probabilidad de victoria hay que perder de media en una fase para que
#: sea una debilidad y no el desgaste normal de jugar. Por debajo de esto no
#: hay nada que arreglar, y llamarlo debilidad solo diluiría las de verdad.
MIN_PHASE_WIN_PERCENT_LOST = 5.0

#: Qué parte de los errores tiene que acumular un tipo para señalarlo. Con
#: cuatro tipos, el reparto ciego es el 25 %: por debajo de un tercio no
#: destaca sobre los demás.
MIN_MISTAKE_TYPE_SHARE = 33.0

#: Cuántos puntos tiene que costar una apertura para entrar en el plan. Se
#: mide con el mismo `points_lost` que el drill de RF-4.2, pero el corte es
#: **más estricto**: el drill admite cualquier línea que cueste algo
#: (`points_lost > 0`, con `MIN_GAMES_TO_DRILL` = 3 partidas) porque ofrece una
#: baraja ordenada por daño y elegir por dónde empezar es de quien entrena;
#: aquí se nombra **una sola** apertura como debilidad de la semana, y decir
#: "tu problema son las francesas" por medio punto perdido sería inventarle un
#: problema.
MIN_OPENING_POINTS_LOST = 1.0

#: Con qué parte de las partidas se considera que los apuros de reloj son un
#: problema propio y no un accidente. El denominador lo pone RF-3.5 y son las
#: partidas analizadas **que traen relojes** (`analyzed_games_with_clocks` en
#: `services/stats.py`), las únicas sobre las que se puede decir nada: contarlo
#: sobre todas las partidas diluiría el porcentaje con las que no se sabe.
MIN_TIME_TROUBLE_SHARE = 30.0

#: Cuántos puntos de precisión hay que haber perdido frente a los meses
#: anteriores para decir que se está yendo a peor. Menos que esto es ruido:
#: la precisión de un mes baila sola.
MIN_ACCURACY_DROP = 2.0


@dataclass(frozen=True)
class Weakness:
    """Algo que se está haciendo mal, con cuánto y de dónde sale.

    `magnitude` es **cuánto de esto hay, en la unidad de su clase** (puntos de
    probabilidad, porcentaje de errores, puntos de marcador…): no hay escala
    común, así que dos clases no se comparan restando sus números, y el nombre
    evita a propósito prometer una gravedad que se pueda medir entre ellas. El
    plan usa el orden en que llegan, nunca la distancia.
    """

    kind: WeaknessKind
    subject: str
    """A qué se refiere: la fase ("middlegame"), el tipo de error ("tactical")
    o el nombre de la apertura. Vacío cuando la debilidad no se refiere a nada
    en concreto (la tendencia, los apuros de reloj)."""
    magnitude: float
    """Cuánto de esto hay, en la unidad de su clase: puntos de probabilidad de
    victoria por jugada en una fase, porcentaje de los errores en un tipo,
    puntos de marcador en una apertura, porcentaje de partidas con apuros,
    puntos de precisión perdidos en la tendencia."""
    color: str = ""
    """Con qué bando duele, **solo en las aperturas**: la Caro-Kann de negras y
    la de blancas son dos debilidades distintas, se estudian por separado y el
    drill que sale de cada una es otro. Vacío en las demás clases, donde el
    color no distingue nada."""


def detect_weaknesses(
    *,
    average_win_percent_lost_by_phase: dict[str, float],
    mistake_share_by_type: dict[str, float],
    opening_points_lost: list[tuple[str, str, float]],
    time_trouble_share: float,
    accuracy_change: float | None,
) -> list[Weakness]:
    """Las debilidades detectadas, en orden de por dónde conviene empezar.

    **Ese orden es fijo y no sale de los números**: fase, tipo de error,
    apertura, apuros de reloj y tendencia. No puede salir de los números
    porque `magnitude` se mide en una unidad distinta en cada clase —perder 8
    puntos de probabilidad por jugada y que el 55 % de los errores sean
    tácticos no son cantidades que se puedan comparar—, así que ordenarlas por
    él sería inventar una escala común. El orden que hay es editorial y va de
    lo más estructural a lo más circunstancial: dónde se pierde la partida,
    luego por qué se pierde, luego en qué apertura concreta, y al final los
    hábitos.

    Cada argumento sale de un requerimiento de RF-3 ya entregado y llega ya
    agregado: la fase donde se pierde ventaja (RF-3.3), el reparto de tipos de
    error (RF-3.4), lo que cuesta cada apertura (RF-3.2), los apuros de reloj
    (RF-3.5) y la tendencia de precisión (RF-3.7).

    Se devuelven **solo las que pasan su umbral**: un plan que enumera cinco
    debilidades siempre, las tenga o no, no ayuda a decidir por dónde empezar.
    """
    detected: list[Weakness] = []

    worst_phase = _highest_item(average_win_percent_lost_by_phase)
    if worst_phase and worst_phase[1] >= MIN_PHASE_WIN_PERCENT_LOST:
        detected.append(Weakness(kind="phase", subject=worst_phase[0], magnitude=worst_phase[1]))

    worst_type = _highest_item(mistake_share_by_type)
    if worst_type and worst_type[1] >= MIN_MISTAKE_TYPE_SHARE:
        detected.append(
            Weakness(kind="mistake_type", subject=worst_type[0], magnitude=worst_type[1])
        )

    worst_opening = max(sorted(opening_points_lost), key=lambda row: row[2], default=None)
    if worst_opening is not None and worst_opening[2] >= MIN_OPENING_POINTS_LOST:
        opening_name, color, points_lost = worst_opening
        detected.append(
            Weakness(kind="opening", subject=opening_name, magnitude=points_lost, color=color)
        )

    if time_trouble_share >= MIN_TIME_TROUBLE_SHARE:
        detected.append(Weakness(kind="time_trouble", subject="", magnitude=time_trouble_share))

    if accuracy_change is not None and accuracy_change <= -MIN_ACCURACY_DROP:
        detected.append(Weakness(kind="accuracy_trend", subject="", magnitude=-accuracy_change))

    return detected


def _highest_item(values: dict[str, float]) -> tuple[str, float] | None:
    """El par con el valor más alto, o `None` si no hay ninguno.

    Ordenar antes de comparar es lo que decide los empates: `max` se queda con
    el primero de los iguales, así que empatar sale por orden alfabético y dos
    ejecuciones con los mismos datos dan el mismo plan. Es la misma forma con
    la que se elige la peor apertura, que llega en tuplas y no en un dict.
    """
    return max(sorted(values.items()), key=lambda item: item[1], default=None)


#: Qué entrenamiento le toca a cada clase de debilidad. Es el corazón de
#: RF-4.5: sin esta tabla, "generado a partir de las debilidades detectadas"
#: no significa nada.
#:
#: - Lo **táctico** y el **medio juego** se entrenan con puzzles, que son
#:   posiciones sueltas donde había algo que ver (RF-4.1).
#: - Lo **posicional** y la **apertura** se entrenan repitiendo líneas
#:   (RF-4.2): un error posicional temprano casi siempre es de repertorio.
#: - El **final** se entrena re-jugando las posiciones donde se perdió
#:   (RF-4.4): un final no se recuerda de memoria, se juega.
#: - Los **apuros de reloj** y la **precisión que cae** se entrenan jugando
#:   partidas enteras contra el motor (RF-4.3), que es lo único que reproduce
#:   la fatiga de una partida de verdad.
_TASK_BY_WEAKNESS: dict[tuple[WeaknessKind, str], TrainingTaskKind] = {
    ("phase", "opening"): "drills",
    ("phase", "middlegame"): "puzzles",
    ("phase", "endgame"): "replays",
    ("mistake_type", "tactical"): "puzzles",
    ("mistake_type", "positional"): "drills",
    ("mistake_type", "endgame"): "replays",
    ("mistake_type", "time"): "sparring",
    ("opening", ""): "drills",
    ("time_trouble", ""): "sparring",
    ("accuracy_trend", ""): "sparring",
}


def _task_for_weakness(weakness: Weakness) -> TrainingTaskKind | None:
    """Qué hay que entrenar para arreglar esa debilidad, o `None` si no hay
    forma de entrenarla con lo que existe hoy."""
    subject = weakness.subject if weakness.kind in ("phase", "mistake_type") else ""
    return _TASK_BY_WEAKNESS.get((weakness.kind, subject))


@dataclass(frozen=True)
class PlanTask:
    """Un deber de la semana: qué entrenar, cuánto y por qué."""

    kind: TrainingTaskKind
    weekly_target: int
    """Cuántos hacer de aquí al domingo. Nunca más de los que hay disponibles:
    un plan que pide treinta puzzles cuando hay cuatro no es exigente, es
    falso."""
    done_this_week: int
    """Cuántos van hechos desde el lunes, de lo que ya está fechado en la base."""
    weaknesses: tuple[Weakness, ...]
    """Las debilidades que piden esta tarea, en el mismo orden en que las
    devuelve `detect_weaknesses`. Más de una cuando varias apuntan al mismo
    entrenamiento, que es lo normal: fallar en el medio juego y fallar por
    táctica suelen ser lo mismo visto de dos maneras."""


#: El tope del `weekly_target` de cada tarea: cuánto se pide de cada cosa
#: cuando hay material de sobra. No son cifras de entrenador, son lo que cabe
#: en una semana sin que el plan se vuelva un trabajo. Lo que de verdad limita
#: cada tarea es cuánto material hay (`available_material`), que casi siempre
#: es menos que esto.
MAX_WEEKLY_TARGETS: dict[TrainingTaskKind, int] = {
    "puzzles": 20,
    "drills": 10,
    "replays": 3,
    "sparring": 2,
}


def build_weekly_tasks(
    weaknesses: list[Weakness],
    available_material: dict[TrainingTaskKind, int],
    done_this_week: dict[TrainingTaskKind, int],
) -> list[PlanTask]:
    """El plan de la semana: una tarea por cada entrenamiento que alguna
    debilidad pida, en el orden en que llegan las debilidades que lo piden
    —el orden fijo de `detect_weaknesses`, no el de sus números, que no son
    comparables entre clases—.

    Sin debilidades no hay plan, y eso **no es un fallo**: significa que no se
    ha detectado nada que arreglar, y llenar la semana igualmente sería
    inventarse el motivo. La pantalla lo dice así.

    Tres cantidades que se parecen y no son la misma: `MAX_WEEKLY_TARGETS` es
    el tope de lo que cabe en una semana, `available_material` es cuánto hay de
    cada cosa —el techo real— y el `weekly_target` de cada tarea es lo que
    finalmente se pide, el menor de los dos. `done_this_week` es lo que ya se
    hizo desde el lunes.
    """
    weaknesses_by_task: dict[TrainingTaskKind, list[Weakness]] = {}
    for weakness in weaknesses:
        task_kind = _task_for_weakness(weakness)
        if task_kind is not None:
            weaknesses_by_task.setdefault(task_kind, []).append(weakness)

    return [
        PlanTask(
            kind=task_kind,
            weekly_target=min(MAX_WEEKLY_TARGETS[task_kind], available_material.get(task_kind, 0)),
            done_this_week=done_this_week.get(task_kind, 0),
            weaknesses=tuple(task_weaknesses),
        )
        for task_kind, task_weaknesses in weaknesses_by_task.items()
        if available_material.get(task_kind, 0) > 0
    ]


def week_start(now: dt.datetime) -> dt.datetime:
    """El lunes de la semana de `now`, a las cero horas.

    La semana empieza en lunes y no "hace siete días" para que el plan sea el
    mismo durante toda la semana: con una ventana móvil, lo hecho el lunes
    dejaría de contar el martes siguiente y el avance bajaría solo.
    """
    monday = now - dt.timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)

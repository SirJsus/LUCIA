"""Entrenamiento a partir de los errores propios (RF-4.1): cuándo toca repasar
un puzzle y qué respuestas se le aceptan.

Las dos reglas viven aquí, puras y sin base de datos, porque son el corazón de
lo que hace útil al entrenamiento y tienen que poder probarse solas (RNF-8):

- **Cuándo vuelve un puzzle**: SM-2, el algoritmo de repetición espaciada de
  SuperMemo que usa Anki. Ver `next_review`.
- **Qué cuenta como acertar** (RF-10.3): no solo la jugada favorita del motor,
  sino cualquiera que pierda lo mismo. Ver `equivalent_solutions`.

Quién lo usa: `lucia_api.services.review`, que reparte con `next_review` y
`grade_of` **los dos** ejercicios —los puzzles de RF-4.1 y las líneas de
apertura de RF-4.2—, porque un drill se repasa como se repasa un puzzle y no
hay dos algoritmos de repaso que mantener. `equivalent_solutions`, en cambio,
es solo de los puzzles (`lucia_api.services.training`) — en una línea de
apertura la respuesta es una y la dicen los maestros.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal

ReviewGrade = Literal["failed", "hesitant", "solved"]
"""Cómo le fue al usuario con el puzzle: falló y vio la solución, acertó tras
intentarlo más de una vez, o acertó a la primera."""

#: Calidad de SM-2 (0-5) de cada resultado. El algoritmo separa en 3: por
#: debajo se considera que no se recordó y el intervalo vuelve a empezar.
#: Acertar al segundo intento es justo la frontera —cuenta como recordado,
#: pero baja un poco la facilidad—, y acertar a la primera es la respuesta
#: limpia que la sube.
_QUALITY_BY_GRADE: dict[ReviewGrade, int] = {"failed": 0, "hesitant": 3, "solved": 5}

#: Por debajo de esto la facilidad no baja más. Es el suelo del SM-2 original:
#: sin él, un puzzle fallado muchas veces se pediría todos los días para
#: siempre y acabaría tapando a los demás.
_MIN_EASE_FACTOR = 1.3

#: Intervalos fijos de los dos primeros aciertos, en días. A partir del
#: tercero el intervalo lo multiplica la facilidad, que es lo que hace que un
#: puzzle bien sabido se vaya espaciando solo.
_FIRST_INTERVAL_DAYS = 1
_SECOND_INTERVAL_DAYS = 6


@dataclass(frozen=True)
class SpacedRepetitionState:
    """Lo que hay que recordar de un puzzle entre repaso y repaso (SM-2).

    No incluye la fecha del próximo repaso: eso es `interval_days` contado
    desde el momento del repaso, y quien persiste sabe qué hora es. Así estas
    funciones no dependen del reloj y se pueden probar sin congelarlo.
    """

    repetitions: int = 0
    """Aciertos seguidos. Vuelve a cero al fallar, y es lo que decide si toca
    intervalo fijo (los dos primeros) o multiplicar por la facilidad."""
    interval_days: int = 0
    """Días entre este repaso y el siguiente. Cero en un puzzle recién
    generado: toca ya."""
    ease_factor: float = 2.5
    """Cuánto se multiplica el intervalo en cada acierto. 2.5 es el valor de
    partida de SM-2; sube con los aciertos y baja con los fallos, de modo que
    un puzzle que cuesta se repite más a menudo que uno fácil."""


NEW_REVIEW_STATE = SpacedRepetitionState()
"""El estado de un ejercicio que nunca se ha repasado: toca hoy. Lo
estrenan por igual los puzzles (RF-4.1) y los drills de apertura (RF-4.2)."""


def next_review(state: SpacedRepetitionState, grade: ReviewGrade) -> SpacedRepetitionState:
    """El estado del puzzle después de repasarlo, según SM-2.

    Al fallar se reinicia la cuenta de aciertos y el puzzle vuelve al día
    siguiente, pero **la facilidad no se reinicia**: se arrastra entre fallos,
    que es lo que hace que un puzzle que se falla una y otra vez acabe
    repitiéndose casi a diario mientras que uno fallado una vez recupere su
    ritmo enseguida.
    """
    quality = _QUALITY_BY_GRADE[grade]
    ease_factor = _adjusted_ease_factor(state.ease_factor, quality)

    if quality < 3:
        return replace(state, repetitions=0, interval_days=1, ease_factor=ease_factor)

    repetitions = state.repetitions + 1
    if repetitions == 1:
        interval_days = _FIRST_INTERVAL_DAYS
    elif repetitions == 2:
        interval_days = _SECOND_INTERVAL_DAYS
    else:
        interval_days = round(state.interval_days * ease_factor)
    return SpacedRepetitionState(
        repetitions=repetitions, interval_days=interval_days, ease_factor=ease_factor
    )


def grade_of(correct: bool, mistakes: int) -> ReviewGrade:
    """Cómo fue el ejercicio, en el vocabulario de SM-2.

    `mistakes` es cuántas veces se falló **antes** de cerrarlo: cero es haberlo
    hecho limpio. Una sola convención para los dos ejercicios, porque cada uno
    llevaba la suya —el puzzle contaba intentos desde 1 y el drill fallos desde
    0— y eran la misma regla escrita dos veces con un desfase de uno.

    Rendirse es fallar, hacerlo limpio es acertar, y tropezar por el camino
    queda en medio: cuenta como recordado, pero baja la facilidad.

    Quién llama y con qué, que es donde estaba el desfase: el puzzle
    (`services/training.py`) cuenta **intentos** empezando en 1, así que pasa
    `attempt_number - 1`; el drill (`routers/drills.py`) ya cuenta **fallos**
    desde 0 y pasa los suyos tal cual. En los dos, `correct=False` cubre por
    igual fallar y rendirse: para SM-2 son lo mismo, no se recordó.
    """
    if not correct:
        return "failed"
    return "solved" if mistakes == 0 else "hesitant"


def _adjusted_ease_factor(ease_factor: float, quality: int) -> float:
    """La fórmula de SM-2 para mover la facilidad: la respuesta perfecta la
    sube 0,1 y cada escalón por debajo la baja cada vez más."""
    penalty = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    return max(_MIN_EASE_FACTOR, ease_factor + penalty)


#: Cuánta probabilidad de victoria puede perder una jugada respecto a la mejor
#: y seguir contando como solución (RF-10.3). Es el mismo margen con el que
#: `lucia_core.classification` llama "excelente" a una jugada
#: (`ClassificationThresholds.excellent_max_loss`), y a propósito: lo que el
#: análisis no considera un error tampoco puede serlo en un puzzle sacado de
#: ese mismo análisis.
#:
#: En probabilidad de victoria y no en centipeones porque 30 centipeones no
#: valen lo mismo en una posición igualada que en una perdida, y es la unidad
#: en la que ya se mide todo lo demás (RF-2.3).
EQUIVALENT_MOVE_MAX_WIN_PERCENT_LOSS = 2.0


def equivalent_solutions(
    candidates: Sequence[tuple[str, float]],
    max_win_percent_loss: float = EQUIVALENT_MOVE_MAX_WIN_PERCENT_LOSS,
) -> tuple[str, ...]:
    """Qué jugadas se aceptan como solución del puzzle (RF-10.3).

    `candidates` son las líneas que el motor veía en esa posición, como pares
    `(jugada en UCI, probabilidad de victoria de quien mueve)`. Se acepta la
    mejor y toda la que no pierda más de `max_win_percent_loss` respecto a
    ella; salen ordenadas de mejor a peor, así que la primera es la del motor.

    Exigir la única jugada favorita del motor enseñaría a adivinar su gusto y
    no a jugar bien: cuando tres jugadas sostienen igual la posición, las tres
    son la respuesta correcta. Con una sola línea guardada —o ninguna, en un
    análisis anterior a RF-10.1— esto devuelve esa única jugada, que es lo
    máximo que se puede afirmar con ese material.
    """
    if not candidates:
        return ()
    best_win_percent = max(win_percent for _uci, win_percent in candidates)
    accepted = [
        (uci, win_percent)
        for uci, win_percent in candidates
        if best_win_percent - win_percent <= max_win_percent_loss
    ]
    accepted.sort(key=lambda candidate: candidate[1], reverse=True)
    return tuple(uci for uci, _win_percent in accepted)

"""Extractores de patrones sobre partidas ya analizadas (RF-2.8, RF-3.4, RF-3.5).

Aquí no se consulta al motor: todo sale de lo que el análisis ya guardó —la
clasificación de cada jugada, su probabilidad de victoria antes y después, las
alternativas que proponía el motor (RF-10.1) y el reloj de chess.com (RF-1.2)—.
Por eso vive en `lucia_core` y no en la API: son reglas de ajedrez y de lectura
de partidas, no consultas a una base de datos. Que los patrones se deduzcan al
leer en vez de persistirse está razonado en ADR-0008; el material lo prepara
`lucia_api.services.insights`, que es quien habla con la base.

**Los umbrales son explícitos y ajustables**, como en `lucia_core.phases` y en
`lucia_core.classification`, por la misma razón: cuando un resultado sorprenda,
tiene que poder explicarse con una regla escrita, no con una intuición metida
en el código.

Qué extrae cada cosa:

- **Momentos críticos** (RF-2.8): las posiciones donde la partida se decidía.
  Son las que merece la pena volver a mirar, y las que sirven de material para
  los puzzles de RF-4.1.
- **Tipo de error** (RF-3.4): por qué se falló, no solo cuánto. "Diez blunders"
  no dice qué entrenar; "seis de ellos con menos de veinte segundos" sí.
- **Apuros de tiempo** (RF-3.5): cómo cae la calidad de juego según baja el
  reloj.
- **Evaluación al salir de la apertura** (lo que faltaba de RF-3.2): con qué
  posición se sale del repertorio.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

from lucia_core.classification import MoveClassification
from lucia_core.phases import Phase

#: Clasificaciones que cuentan como error para los extractores. `book` y las
#: buenas no entran, y `missed_win` sí: dejar escapar un mate es un error del
#: que se aprende algo.
MISTAKE_CLASSIFICATIONS: frozenset[MoveClassification] = frozenset(
    {"inaccuracy", "mistake", "blunder", "missed_win"}
)


@dataclass(frozen=True)
class MoveContext:
    """Una jugada analizada con todo lo que hace falta para buscarle patrones.

    Es un tipo propio y no `analysis.AnalyzedMove` porque el material llega de
    la base, no del motor: incluye el reloj (que el análisis no conoce) y trae
    las alternativas ya traducidas a probabilidad de victoria, que es la unidad
    en la que se comparan (RF-2.3).

    Todos los porcentajes van **desde el punto de vista de quien juega la
    jugada**, no desde el de las blancas: un patrón es de quien lo comete.
    """

    ply: int
    color: str
    """"white" | "black": de quién es la jugada. Los porcentajes van desde su
    punto de vista, así que sin esto no se pueden volver a mirar desde el de
    las blancas, que es como los enseña la interfaz."""
    san: str
    classification: MoveClassification
    phase: Phase
    accuracy: float
    win_percent_before: float
    win_percent_after: float
    alternative_win_percents: tuple[float, ...] = ()
    """Probabilidad de victoria de cada línea que proponía el motor en la
    posición previa, de mejor a peor. Vacío si ese análisis no guardó
    alternativas."""
    best_alternative_san: str | None = None
    """La jugada que el motor recomendaba, en notación algebraica: de ella se
    deduce si el error era táctico (una captura o un jaque concretos)."""
    seconds_left: float | None = None
    """Reloj del jugador **tras** la jugada, en segundos. `None` si la partida
    no trae relojes (`%clk`), como las importadas de otras fuentes."""


@dataclass(frozen=True)
class InsightThresholds:
    """Los números con los que se decide qué es un patrón y qué es ruido."""

    only_move_gap: float = 10.0
    """Cuánta probabilidad de victoria tiene que sacarle la mejor línea a la
    segunda para que la posición sea de "jugada única"."""
    swing_change: float = 15.0
    """Cuánto tiene que moverse la probabilidad de victoria, además de cruzar
    el 50 %, para que sea un vuelco. Sin este mínimo, pasar de 51 % a 49 %
    contaría como que la partida cambió de manos."""
    winning_win_percent: float = 75.0
    """A partir de aquí la posición se considera ganada."""
    lost_chance_win_percent: float = 60.0
    """Si tras la jugada se baja de aquí teniendo una ganada, la ocasión se
    dio por perdida."""
    time_trouble_seconds: float = 20.0
    """Por debajo de este reloj se juega con apuros. Es absoluto a propósito:
    un porcentaje del control de tiempo metería en "apuros" media partida por
    correspondencia, donde quedan horas."""


DEFAULT_THRESHOLDS = InsightThresholds()

CriticalMomentKind = Literal["only_move", "swing", "missed_chance"]

MistakeType = Literal["time", "tactical", "endgame", "positional"]


@dataclass(frozen=True)
class CriticalMoment:
    """Una posición donde la partida se decidía (RF-2.8)."""

    ply: int
    color: str
    san: str
    kinds: tuple[CriticalMomentKind, ...]
    """Por qué es crítica; puede ser por más de un motivo a la vez."""
    win_percent_before: float
    win_percent_after: float
    best_alternative_san: str | None


def critical_moments(
    moves: list[MoveContext], thresholds: InsightThresholds | None = None
) -> list[CriticalMoment]:
    """Las posiciones donde la partida se decidía, en orden de jugada.

    Tres motivos, que pueden darse a la vez:

    - **Jugada única**: el motor solo veía una forma de sostener la posición
      —su mejor línea le saca `only_move_gap` puntos a la segunda—. Es lo que
      distingue "aquí había que encontrar algo" de "aquí valían tres jugadas".
      Necesita las alternativas de RF-10.1; sin ellas no se puede afirmar.
    - **Vuelco**: la jugada cruzó el 50 % de lado a lado. La partida cambió de
      manos ahí.
    - **Ocasión perdida**: se tenía una posición ganada y se dejó escapar.

    Que una posición sea crítica no significa que se jugara mal: la jugada
    única encontrada también es un momento crítico, y saberlo es la mitad de
    lo que se viene a aprender.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    moments: list[CriticalMoment] = []
    for move in moves:
        kinds: list[CriticalMomentKind] = []
        if _is_only_move(move, thresholds):
            kinds.append("only_move")
        if _is_swing(move, thresholds):
            kinds.append("swing")
        if _is_missed_chance(move, thresholds):
            kinds.append("missed_chance")
        if kinds:
            moments.append(
                CriticalMoment(
                    ply=move.ply,
                    color=move.color,
                    san=move.san,
                    kinds=tuple(kinds),
                    win_percent_before=move.win_percent_before,
                    win_percent_after=move.win_percent_after,
                    best_alternative_san=move.best_alternative_san,
                )
            )
    return moments


def _is_only_move(move: MoveContext, thresholds: InsightThresholds) -> bool:
    if len(move.alternative_win_percents) < 2:
        return False  # sin segunda opción no se puede hablar de jugada única
    best, second = move.alternative_win_percents[0], move.alternative_win_percents[1]
    return best - second >= thresholds.only_move_gap


def _is_swing(move: MoveContext, thresholds: InsightThresholds) -> bool:
    """Cruzar el 50 % —de estar mejor a estar peor, o al revés— con un cambio
    que se note. Las dos condiciones hacen falta: solo el cruce metería el
    ruido de una posición que oscila alrededor de la igualdad, y solo la
    magnitud llamaría vuelco a pasar de ganada a menos ganada."""
    crossed_the_middle = (move.win_percent_before - 50) * (move.win_percent_after - 50) < 0
    changed_enough = (
        abs(move.win_percent_before - move.win_percent_after) >= thresholds.swing_change
    )
    return crossed_the_middle and changed_enough


def _is_missed_chance(move: MoveContext, thresholds: InsightThresholds) -> bool:
    """Se tenía una ganada —la posición o la mejor línea del motor— y tras la
    jugada ya no."""
    best_available = max([move.win_percent_before, *move.alternative_win_percents[:1]])
    return (
        best_available >= thresholds.winning_win_percent
        and move.win_percent_after < thresholds.lost_chance_win_percent
    )


def mistake_type(
    move: MoveContext, thresholds: InsightThresholds | None = None
) -> MistakeType | None:
    """Por qué falló esta jugada, o `None` si no fue un error (RF-3.4).

    Cada error recibe **un solo** tipo, y el orden en que se comprueban es la
    decisión de fondo de este extractor:

    1. **Tiempo**, si quedaba poco reloj: con quince segundos en la mano, la
       causa es esa y no la posición.
    2. **Táctico**, si lo que el motor proponía era una captura o un jaque:
       había algo concreto que ver y no se vio.
    3. **Final**, si la partida ya estaba en esa fase: los finales se fallan
       por técnica, no por cálculo.
    4. **Posicional**, el resto: no había una jugada concreta que encontrar,
       se eligió mal el plan.

    El orden va de la causa más específica a la más general, y por eso "final"
    va después de "táctico": que la partida esté en un final es contexto, y
    haber tenido delante una captura ganadora es una causa.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    if move.classification not in MISTAKE_CLASSIFICATIONS:
        return None
    if is_time_trouble(move.seconds_left, thresholds):
        return "time"
    if _is_tactical(move.best_alternative_san):
        return "tactical"
    if move.phase == "endgame":
        return "endgame"
    return "positional"


def is_time_trouble(
    seconds_left: float | None, thresholds: InsightThresholds | None = None
) -> bool:
    """Si ese reloj es ya apuro de tiempo. Una partida sin relojes (`None`)
    nunca lo es: no se puede afirmar lo que no se sabe."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    return seconds_left is not None and seconds_left < thresholds.time_trouble_seconds


def _is_tactical(best_alternative_san: str | None) -> bool:
    """Una captura (`x`) o un jaque (`+`/`#`) en la jugada que el motor
    prefería: había algo concreto que calcular."""
    if not best_alternative_san:
        return False
    return any(mark in best_alternative_san for mark in ("x", "+", "#"))


@dataclass(frozen=True)
class MistakeTypeCount:
    mistake_type: MistakeType
    mistakes: int
    """Cuántos errores de este tipo, contando imprecisiones, errores, blunders
    y mates perdidos."""
    blunders: int
    """De ellos, cuántos fueron blunders: distingue "fallo diez veces poco" de
    "fallo tres veces mucho"."""


def mistakes_by_type(
    moves: list[MoveContext], thresholds: InsightThresholds | None = None
) -> list[MistakeTypeCount]:
    """Distribución de errores por tipo (RF-3.4), del que más al que menos."""
    mistakes: Counter[MistakeType] = Counter()
    blunders: Counter[MistakeType] = Counter()
    for move in moves:
        found_type = mistake_type(move, thresholds)
        if found_type is None:
            continue
        mistakes[found_type] += 1
        if move.classification == "blunder":
            blunders[found_type] += 1
    return [
        MistakeTypeCount(found_type, count, blunders[found_type])
        for found_type, count in mistakes.most_common()
    ]


#: Tramos de reloj en los que se mira la calidad de juego, de más holgado a más
#: apurado. Cada uno es "menos de N segundos restantes"; el último es el de
#: apuros de verdad.
TIME_BUCKET_UPPER_BOUNDS: tuple[float | None, ...] = (None, 60.0, 30.0, 10.0)


@dataclass(frozen=True)
class TimeBucketStats:
    """Calidad de juego con un reloj determinado (RF-3.5)."""

    max_seconds_left: float | None
    """Techo del tramo, o `None` para el tramo holgado (más de un minuto)."""
    moves: int
    average_accuracy: float
    mistakes: int
    blunders: int


def time_pressure(moves: list[MoveContext]) -> list[TimeBucketStats]:
    """Cómo cae la calidad de juego según baja el reloj (RF-3.5).

    Solo entran las jugadas con reloj conocido: las partidas sin `%clk` no
    dicen nada de esto y contarlas como "tiempo de sobra" mentiría.
    """
    moves_by_bucket: dict[float | None, list[MoveContext]] = {}
    for move in moves:
        if move.seconds_left is not None:
            moves_by_bucket.setdefault(_bucket_of(move.seconds_left), []).append(move)
    return [
        TimeBucketStats(
            max_seconds_left=upper_bound,
            moves=len(in_bucket),
            average_accuracy=sum(move.accuracy for move in in_bucket) / len(in_bucket),
            mistakes=sum(1 for move in in_bucket if move.classification in MISTAKE_CLASSIFICATIONS),
            blunders=sum(1 for move in in_bucket if move.classification == "blunder"),
        )
        for upper_bound in TIME_BUCKET_UPPER_BOUNDS
        if (in_bucket := moves_by_bucket.get(upper_bound))
    ]


def _bucket_of(seconds_left: float) -> float | None:
    """El tramo más apurado en el que cabe ese reloj, o `None` si no baja de
    ninguno: ese es el tramo holgado."""
    return min(
        (bound for bound in TIME_BUCKET_UPPER_BOUNDS if bound is not None and seconds_left < bound),
        default=None,
    )


def opening_exit_win_percent(moves: list[MoveContext]) -> float | None:
    """Con qué posición se sale de la apertura (lo que faltaba de RF-3.2).

    Es la probabilidad de victoria tras la última jugada de fase `opening`,
    desde el punto de vista de quien la jugó. `None` si esa partida no tiene
    ninguna jugada del jugador en apertura.
    """
    opening_moves = [move for move in moves if move.phase == "opening"]
    if not opening_moves:
        return None
    return max(opening_moves, key=lambda move: move.ply).win_percent_after

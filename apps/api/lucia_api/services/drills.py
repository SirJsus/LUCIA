"""Drill de aperturas (RF-4.2): generar las líneas que hay que repetir y
cargarlas para recorrerlas.

La cola de repaso y el apunte de cómo fue cada pasada no están aquí sino en
`services/review.py`, el mismo que reparte los puzzles: un drill se repasa
como se repasa un puzzle.

Este módulo es el puente entre lo que ya se sabe del jugador y
`lucia_core.drills`, igual que `services/training.py` lo es con
`lucia_core.training`. Aquí se carga el material y allí viven las reglas
puras: por dónde va la línea, qué jugada toca y qué cuenta como "rendir peor".

**Las dos barajas** que pide RF-4.2, con el mismo drill detrás:

- **Salidas de la teoría** (`source="departure"`, de RF-3.6): los puntos donde
  se abandona el libro una y otra vez. La línea recorre la apertura como se
  jugó y termina en la jugada de maestros que había que hacer en lugar de la
  que se hizo.
- **Peores aperturas** (`source="opening"`, de RF-3.2): las aperturas que
  cuestan puntos. La línea es la de una partida propia de esa apertura, con la
  misma corrección en el punto donde se sale del libro.

Las dos se construyen igual —camino propio, corrección de maestros— y se
diferencian en **qué se elige y por qué**, que es lo que la pantalla cuenta.
Que la línea no continúe más allá de la salida es deliberado: seguir la línea
principal de los maestros pediría posiciones que RF-3.6 nunca consulta, y la
caché del explorador se llena despacio y a propósito (ADR-0010).

**Generar no sale a la red.** Usa lo que la caché del explorador ya sepa, como
`compare_repertoire`; si falta teoría, faltan drills, y la pantalla lo dice y
manda a refrescar el repertorio. Es la misma regla de siempre.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import chess
from lucia_core.drills import DrillLine, is_worth_drilling, line_uci_from_departure, points_lost
from lucia_core.openings import Opening, identify_opening
from lucia_core.training import NEW_REVIEW_STATE
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import OpeningDrill
from lucia_api.services.repertoire import RepertoireComparison, compare_repertoire
from lucia_api.services.stats import MAX_OPENINGS_CONSIDERED, OpeningStats, get_player_stats


@dataclass(frozen=True)
class DrillGeneration:
    """Qué dejó una generación: cuántas líneas nuevas y cuánta teoría faltaba
    al mirar. Las dos salen del mismo repaso al repertorio, y por eso van
    juntas: preguntarlas por separado costaría compararlo dos veces."""

    created: int
    positions_missing: int


async def generate_drills(session: AsyncSession, username: str) -> DrillGeneration:
    """Crea los drills que falten y dice cuántos se crearon.

    Es idempotente: la clave `(bando, línea)` es única, así que volver a
    pulsar tras jugar o analizar más partidas añade solo lo nuevo y **no toca
    el estado de repaso de lo que ya había**, igual que generar puzzles.
    """
    comparison = await compare_repertoire(session, username)
    stats = await get_player_stats(session, username, limit_openings=MAX_OPENINGS_CONSIDERED)
    existing = {
        (color, line)
        for color, line in (
            await session.execute(select(OpeningDrill.player_color, OpeningDrill.line_uci))
        ).all()
    }

    created = 0
    candidates = sorted(
        _candidate_drills(comparison, stats.by_opening),
        key=lambda drill: points_lost(drill.games_played, drill.score_percent),
        reverse=True,
    )
    for drill in candidates:
        if (drill.player_color, drill.line_uci) in existing:
            continue
        existing.add((drill.player_color, drill.line_uci))
        session.add(drill)
        created += 1

    await session.commit()
    return DrillGeneration(created=created, positions_missing=comparison.positions_missing)


def _opening_of(line_uci: tuple[str, ...]) -> Opening | None:
    """Cómo se llama la apertura a la que lleva esa línea, con la tabla ECO
    propia (`lucia_core.openings`), que es la misma con la que se nombran las
    aperturas de las partidas (RF-3.2). `None` si la línea se sale del libro
    antes de tener nombre, que es lo que pasa en las salidas más tempranas."""
    return identify_opening(chess.Board(), [chess.Move.from_uci(uci) for uci in line_uci]).opening


def _candidate_drills(
    comparison: RepertoireComparison, by_opening: list[OpeningStats]
) -> Iterator[OpeningDrill]:
    """Las líneas que merecen entrenarse, de las dos barajas, sin guardar.

    Las dos salen de las **mismas** salidas de la teoría y por eso se recorren
    a la vez; lo que cambia es el motivo por el que una línea entra:

    - Por sí misma (`"departure"`, RF-3.6) cuando se abandona el libro ahí una
      y otra vez y eso cuesta puntos.
    - Por su apertura (`"opening"`, RF-3.2) cuando la apertura a la que lleva
      es de las que cuestan puntos. Una apertura que va mal pero en la que
      nunca se abandona el libro no da drill, y es honesto que no lo dé: ahí
      el problema no es la apertura, es lo que viene después, y eso son los
      puzzles de RF-4.1.

    El motivo que se guarda en cada caso es el suyo —las partidas de la salida
    o las de la apertura—, porque es lo que la pantalla va a contar y tiene que
    cuadrar con lo que dicen las estadísticas.

    Se descarta la salida de la que no se pueda afirmar ninguna respuesta: sin
    jugada de maestros no hay nada que enseñar, y un drill sin solución solo
    enseñaría a adivinar. Es la misma regla con la que RF-10.3 decide que un
    error sin respuesta no genera puzzle.
    """
    worst_openings = {
        (opening.opening, opening.color): opening.record
        for opening in by_opening
        if is_worth_drilling(opening.record.total, opening.record.score_percent)
    }
    for departure in comparison.departures:
        if not departure.master_moves_uci:
            continue
        line_uci = line_uci_from_departure(
            departure.preceding_moves_uci,
            departure.ply,
            # La más jugada por los maestros: la línea principal es la que se
            # viene a aprender, no una alternativa defendible.
            departure.master_moves_uci[0],
        )
        opening = _opening_of(line_uci)

        if is_worth_drilling(departure.games, departure.score_percent):
            yield _new_drill(
                "departure",
                departure.color,
                line_uci,
                opening,
                departure.games,
                departure.score_percent,
            )
        record = worst_openings.get((opening.name, departure.color)) if opening else None
        if record is not None:
            yield _new_drill(
                "opening", departure.color, line_uci, opening, record.total, record.score_percent
            )


def _new_drill(
    source: str,
    player_color: str,
    line_uci: tuple[str, ...],
    opening: Opening | None,
    games_played: int,
    score_percent: float,
) -> OpeningDrill:
    """La fila de un drill recién nacido: su línea, de qué baraja sale y un
    estado de repaso de estreno, el mismo con el que empieza un puzzle."""
    return OpeningDrill(
        source=source,
        player_color=player_color,
        line_uci=" ".join(line_uci),
        opening_eco=opening.eco if opening else None,
        opening_name=opening.name if opening else None,
        games_played=games_played,
        score_percent=score_percent,
        repetitions=NEW_REVIEW_STATE.repetitions,
        interval_days=NEW_REVIEW_STATE.interval_days,
        ease_factor=NEW_REVIEW_STATE.ease_factor,
    )


def drill_line(drill: OpeningDrill) -> DrillLine:
    """La línea del drill en la forma que sabe recorrerla (`lucia_core.drills`)."""
    return DrillLine(
        moves_uci=tuple(drill.line_uci.split()),
        player_color=chess.WHITE if drill.player_color == "white" else chess.BLACK,
    )


async def count_drills(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(OpeningDrill)) or 0

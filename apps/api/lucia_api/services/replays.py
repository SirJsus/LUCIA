"""Re-jugar desde el error (RF-4.4): qué posiciones de las partidas propias
merecen retomarse contra el motor.

Este módulo **solo elige**: la partida que sale de aquí la abre
`services/sparring.py`, porque retomar una partida es jugar contra el motor
desde otra posición y no una forma distinta de jugar (RF-4.3 y RF-4.4
comparten tabla, ciclo y pantalla de juego).

**No se guarda nada.** La lista se deduce al leer los análisis que ya hay,
como los patrones de RF-3 y por la misma razón
([ADR-0008](../../../../docs/adr/0008-patrones-deducidos-al-leer.md)): no
lleva encima ningún estado propio —ni repasos, ni progreso— así que
persistirla solo daría una segunda copia que podría quedarse vieja cuando se
reanaliza una partida. Es la decisión contraria a la de los puzzles (RF-4.1) y
los drills (RF-4.2), que sí se guardan porque arrastran historial de repaso.

Qué posiciones se ofrecen: los **errores propios graves** de los análisis
terminados más recientes, los mismos que dan puzzle (`PUZZLE_CLASSIFICATIONS`)
y por los mismos motivos. Desde el visor se puede retomar cualquier posición
de cualquier partida; esta lista es la versión curada, la que responde a "¿por
dónde empiezo?".

Todo lo de arriba está razonado en
[ADR-0020](../../../../docs/adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md),
incluido por qué esto no invade RF-11.1.
"""

from __future__ import annotations

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.services.games import player_color, player_side
from lucia_api.services.insights import latest_analysis_ids
from lucia_api.services.training import PUZZLE_CLASSIFICATIONS


def _own_serious_mistake_ids(username: str) -> Select[tuple[int]]:
    """Los `AnalyzedMove.id` que definen la lista: errores propios graves de los
    análisis terminados más recientes. Sale aparte porque lo comparten las dos
    consultas —la de las posiciones y la de cuántas hay—, y dos filtros escritos
    dos veces son dos filtros que divergen."""
    return (
        select(AnalyzedMove.id)
        .join(Analysis, AnalyzedMove.analysis_id == Analysis.id)
        .where(
            Analysis.id.in_(latest_analysis_ids()),
            AnalyzedMove.classification.in_(PUZZLE_CLASSIFICATIONS),
            # Las del rival no entran: dicen cómo juega el otro, no qué hay
            # que rehacer.
            AnalyzedMove.color == player_color(username),
        )
    )


async def count_replay_positions(session: AsyncSession, username: str) -> int:
    """Cuántos errores propios hay en total, sin el recorte de `limit`.

    Viaja con la lista porque sin él la pantalla enseña veinte de trescientos y
    nada dice que haya más, mientras las dos pestañas hermanas que reparten cola
    —puzzles y aperturas— dicen siempre cuántas quedan de cuántas (fila 102 del
    inventario de docs/07-coherencia-ui.md, criterio C-3). La quinta, el
    sparring, no entra en la comparación: lista partidas abiertas y no una cola.
    """
    total = await session.scalar(
        select(func.count()).select_from(_own_serious_mistake_ids(username).subquery())
    )
    return total or 0


async def replay_positions(
    session: AsyncSession, username: str, limit: int
) -> list[Row[tuple[AnalyzedMove, Game, str]]]:
    """Los errores propios desde los que se puede retomar, del más caro al más
    barato: lo que más costó es por donde tiene sentido empezar.

    Cada fila trae la jugada que se torció, la partida en la que se jugó y
    contra quién —el bando contrario al que se llevaba—, que es con lo que
    `routers/replays.py` arma la respuesta.
    """
    rows = await session.execute(
        select(
            AnalyzedMove,
            Game,
            player_side(username, Game.black_username, Game.white_username).label("opponent"),
        )
        .join(Analysis, AnalyzedMove.analysis_id == Analysis.id)
        .join(Game, Analysis.game_id == Game.id)
        .where(AnalyzedMove.id.in_(_own_serious_mistake_ids(username)))
        # Lo que costó el error, en probabilidad de victoria de quien lo
        # cometió: es lo que dice por cuál empezar.
        .order_by((AnalyzedMove.win_percent_before - AnalyzedMove.win_percent_after).desc())
        .limit(limit)
    )
    return list(rows.all())

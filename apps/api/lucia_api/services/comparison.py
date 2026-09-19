"""Comparación de dos análisis de la misma partida (RF-2.6).

Stockfish y Lc0 no discrepan por capricho: Stockfish busca por fuerza bruta
con evaluación NNUE, y Lc0 explora con una red que "intuye" el valor
posicional. Donde los dos coinciden, la jugada suele estar clara; donde
discrepan es donde hay algo que entender, y eso es lo que este módulo
localiza.

**Cada discrepancia se acompaña de la W/D/L que da cada motor**, que es la otra
mitad de RF-2.6. La distancia en probabilidad de victoria dice *cuánto* se
separan, pero no *en qué*: sale de convertir el centipeón con una fórmula
común, así que dos motores que discrepan en centipeones discrepan ahí por
definición. La W/D/L la contesta cada motor por su cuenta, y es donde se ve el
desacuerdo de verdad — el caso que motiva el requerimiento es la posición que
Stockfish puntúa como ganada y la red de Lc0 ve como tablas técnicas.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove
from lucia_api.services.analysis import LineWdl

#: Diferencia de probabilidad de victoria (0-100) a partir de la cual se
#: considera que los motores discrepan de verdad. Por debajo es ruido: dos
#: motores nunca dan exactamente el mismo número.
DEFAULT_DISAGREEMENT_THRESHOLD = 10.0


@dataclass
class MoveComparison:
    ply: int
    color: str
    san: str
    """Clasificación y evaluación según cada motor."""
    classification_a: str
    classification_b: str
    win_percent_after_a: float
    win_percent_after_b: float
    best_move_a: str | None
    best_move_b: str | None
    wdl_after_a: LineWdl | None = None
    wdl_after_b: LineWdl | None = None
    """Lo que cada motor da como W/D/L de la posición que deja esta jugada
    (RF-2.6). `None` en la última jugada de la partida —no hay posición
    siguiente de la que se guardaran líneas— y en los análisis anteriores a
    que se le pidiera la W/D/L al motor."""

    @property
    def win_percent_gap(self) -> float:
        """Cuánto se separan los dos motores al valorar la posición."""
        return abs(self.win_percent_after_a - self.win_percent_after_b)

    @property
    def same_best_move(self) -> bool:
        return self.best_move_a == self.best_move_b


@dataclass
class AnalysisComparison:
    game_id: int
    analysis_a: int
    analysis_b: int
    engine_a: str
    engine_b: str
    total_moves: int
    agreed_best_moves: int
    """En cuántas jugadas ambos motores recomendaban lo mismo."""
    disagreements: list[MoveComparison]
    """Solo las jugadas donde la diferencia supera el umbral, de mayor a menor."""

    @property
    def best_move_agreement_percent(self) -> float:
        if self.total_moves == 0:
            return 0.0
        return self.agreed_best_moves / self.total_moves * 100


class ComparisonError(ValueError):
    """La comparación no tiene sentido: falta un análisis, no ha terminado, o
    son de partidas distintas."""


async def compare_analyses(
    session: AsyncSession,
    analysis_a_id: int,
    analysis_b_id: int,
    threshold: float = DEFAULT_DISAGREEMENT_THRESHOLD,
) -> AnalysisComparison:
    a = await session.get(Analysis, analysis_a_id)
    b = await session.get(Analysis, analysis_b_id)
    if a is None or b is None:
        raise ComparisonError("alguno de los dos análisis no existe")
    if a.game_id != b.game_id:
        raise ComparisonError("los análisis son de partidas distintas")
    if a.status != "done" or b.status != "done":
        raise ComparisonError("ambos análisis tienen que estar terminados")

    moves_a = await _moves_by_ply(session, a.id)
    moves_b = await _moves_by_ply(session, b.id)

    disagreements: list[MoveComparison] = []
    agreed_best_moves = 0
    # Solo los plies presentes en ambos: si un análisis se cortó a medias, la
    # parte que falta no se puede comparar.
    for ply in sorted(set(moves_a) & set(moves_b)):
        move_a, move_b = moves_a[ply], moves_b[ply]
        move_comparison = MoveComparison(
            ply=ply,
            color=move_a.color,
            san=move_a.san,
            classification_a=move_a.classification,
            classification_b=move_b.classification,
            win_percent_after_a=move_a.win_percent_after,
            win_percent_after_b=move_b.win_percent_after,
            best_move_a=move_a.best_move_uci,
            best_move_b=move_b.best_move_uci,
            wdl_after_a=_wdl_after(moves_a, ply),
            wdl_after_b=_wdl_after(moves_b, ply),
        )
        if move_comparison.same_best_move:
            agreed_best_moves += 1
        if move_comparison.win_percent_gap >= threshold:
            disagreements.append(move_comparison)

    disagreements.sort(key=lambda c: c.win_percent_gap, reverse=True)

    return AnalysisComparison(
        game_id=a.game_id,
        analysis_a=a.id,
        analysis_b=b.id,
        engine_a=a.engine,
        engine_b=b.engine,
        total_moves=len(set(moves_a) & set(moves_b)),
        agreed_best_moves=agreed_best_moves,
        disagreements=disagreements,
    )


def _wdl_after(moves_by_ply: dict[int, AnalyzedMove], ply: int) -> LineWdl | None:
    """La W/D/L de la posición que deja la jugada de `ply`, según este análisis.

    No hace falta guardarla aparte: las líneas de una jugada son las de la
    posición **anterior** a ella (RF-10.1), así que la posición posterior a la
    jugada `ply` es justo la anterior a `ply + 1`, y ahí ya está. La mejor
    línea es la primera, que es la que sostiene la evaluación de la posición.
    """
    next_move = moves_by_ply.get(ply + 1)
    if next_move is None or not next_move.alternatives_json:
        return None
    stored_wdl = next_move.alternatives_json[0].get("wdl")
    return LineWdl(*stored_wdl) if stored_wdl else None


async def _moves_by_ply(session: AsyncSession, analysis_id: int) -> dict[int, AnalyzedMove]:
    move_rows = await session.execute(
        select(AnalyzedMove).where(AnalyzedMove.analysis_id == analysis_id)
    )
    return {move.ply: move for move in move_rows.scalars().all()}

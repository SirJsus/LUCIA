"""Patrones de juego de un jugador, sobre lo que ya guardó el análisis
(RF-2.8, RF-3.4, RF-3.5).

Este módulo es el puente entre la base y `lucia_core.insights`: carga las
jugadas analizadas con su contexto —la fase, las alternativas del motor y el
reloj de chess.com— y las convierte en `MoveContext`, que es lo que el núcleo
sabe leer. Las reglas de qué es un momento crítico o de qué tipo es un error
viven allí, no aquí. Nada se persiste ni se vuelve a preguntar al motor: los
patrones se deducen cada vez que se piden, sobre lo guardado (ADR-0008).

Lo consumen `routers/analysis.py` (los momentos críticos de una partida) y
`services/stats.py` (los patrones agregados del jugador).

**Un tablero no cuenta, salvo que sea una partida del usuario.** Lo que se
agrega son partidas: los análisis de tablero (RF-6.9) se quedan fuera en
`latest_analysis_ids`. La excepción de RF-6.5 no se ve desde aquí, porque un
tablero marcado como "partida propia" cuenta *como su partida publicada*, no
como tablero (ADR-0014).

**Una partida cuenta una sola vez.** Una misma partida puede tener análisis de
Stockfish y de Lc0 (RF-2.6); sumar los dos contaría cada jugada dos veces y
diría que se juega el doble de mal. Se toma el análisis terminado más reciente
de cada partida, que es el que la interfaz enseña por defecto.
"""

from __future__ import annotations

from collections.abc import Sequence

import chess
import chess.engine
from lucia_core.accuracy import win_percent
from lucia_core.insights import CriticalMoment, MoveContext, critical_moments
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.services.analysis import alternatives_from_cache, alternatives_of


def latest_analysis_ids():
    """Subconsulta con el análisis terminado más reciente de cada partida.

    `max(id)` y no `max(created_at)` porque el id es monótono y no empata: dos
    análisis encolados en el mismo segundo tienen la misma fecha.

    **Los análisis de tablero quedan fuera** (`game_id` nulo, RF-6.9): un
    tablero de análisis no cuenta en las estadísticas ni en la detección de
    patrones (RF-6.5). Se excluyen aquí y no en cada consulta porque esta
    subconsulta es por donde pasan todas.

    Con una excepción, y por eso el filtro mira `game_id` y no `board_id`: un
    tablero marcado como "partida propia" se publica como una fila de `games`
    y su análisis se enlaza a ella, así que llega aquí con las dos columnas
    llenas y entra como el de cualquier partida. Quién pone y quita ese enlace
    es `services/own_games.py::link_analyses_to_own_game` (ADR-0014); aquí no
    hay nada que distinguir.
    """
    return (
        select(func.max(Analysis.id))
        .where(Analysis.status == "done", Analysis.game_id.is_not(None))
        .group_by(Analysis.game_id)
        .scalar_subquery()
    )


async def player_move_contexts(
    session: AsyncSession, username: str
) -> list[tuple[int, MoveContext]]:
    """Las jugadas *del jugador* en sus partidas analizadas, con su contexto,
    emparejadas con el id de la partida a la que pertenecen.

    Las del rival no entran: dicen más de cómo juega el otro que de uno mismo,
    que es la misma regla que ya sigue el reparto por fases (RF-3.3).
    """
    rows = (
        await session.execute(
            select(AnalyzedMove, Analysis, Game.id, Game.clocks_json, Game.white_username)
            .join(Analysis, AnalyzedMove.analysis_id == Analysis.id)
            .join(Game, Analysis.game_id == Game.id)
            .where(Analysis.id.in_(latest_analysis_ids()))
            .order_by(Game.id, AnalyzedMove.ply)
        )
    ).all()
    player_rows = [
        (move, analysis, game_id, clocks_json)
        for move, analysis, game_id, clocks_json, white_username in rows
        if move.color == ("white" if white_username.lower() == username.lower() else "black")
    ]

    # Las alternativas de un análisis anterior a RF-10 no están en su fila; se
    # rescatan de la caché de posiciones, igual que hace el visor (ADR-0007).
    # Sin ellas no habría forma de saber si un error fue táctico ni si la
    # posición tenía una sola jugada.
    moves_by_analysis: dict[Analysis, list[AnalyzedMove]] = {}
    for move, analysis, _game_id, _clocks_json in player_rows:
        moves_by_analysis.setdefault(analysis, []).append(move)
    cached_by_analysis = {
        analysis.id: await alternatives_from_cache(session, analysis, analysis_moves)
        for analysis, analysis_moves in moves_by_analysis.items()
    }

    return [
        (
            game_id,
            _move_context(
                move, clocks_json, alternatives_of(move, cached_by_analysis[analysis.id])
            ),
        )
        for move, analysis, game_id, clocks_json in player_rows
    ]


def _move_context(
    move: AnalyzedMove, clocks_json: list | None, alternatives: list[dict]
) -> MoveContext:
    """Traduce una fila de `analyzed_moves` al material que lee el núcleo.

    `alternatives` llega aparte porque las de un análisis anterior a RF-10 no
    están en la fila, sino rescatadas de `position_cache`.
    """
    return MoveContext(
        ply=move.ply,
        color=move.color,
        san=move.san,
        classification=move.classification,
        phase=move.phase,
        accuracy=move.move_accuracy,
        win_percent_before=move.win_percent_before,
        win_percent_after=move.win_percent_after,
        alternative_win_percents=tuple(
            _mover_win_percent(line, move.color, move.ply) for line in alternatives
        ),
        best_alternative_san=_best_alternative_san(alternatives, move.fen_before),
        seconds_left=_seconds_left(clocks_json, move.ply),
    )


def _mover_win_percent(serialized_line: dict, color: str, ply: int) -> float:
    """Probabilidad de victoria de una línea guardada, desde el punto de vista
    de quien mueve.

    Las líneas se guardan desde el de las blancas, como todo lo persistido; un
    patrón, en cambio, es de quien lo comete, así que aquí se le da la vuelta
    cuando las juega el negro.
    """
    score_mate, score_cp = serialized_line["score_mate"], serialized_line["score_cp"]
    score = (
        chess.engine.Mate(score_mate) if score_mate is not None else chess.engine.Cp(score_cp or 0)
    )
    white_win_percent = win_percent(score, ply=ply)
    return white_win_percent if color == "white" else 100 - white_win_percent


def _best_alternative_san(alternatives: list[dict], fen_before: str) -> str | None:
    """La jugada que recomendaba el motor, en notación algebraica.

    Se deriva del FEN previo en vez de guardarse (ADR-0007), y hace falta con
    esta forma —no en UCI— porque el tipo de error se decide mirando si esa
    jugada era una captura o un jaque, que es justo lo que la notación
    algebraica dice y la UCI no.
    """
    if not alternatives or not alternatives[0]["pv"]:
        return None
    try:
        board = chess.Board(fen_before)
        return board.san(chess.Move.from_uci(alternatives[0]["pv"][0]))
    except ValueError:
        return None  # FEN o jugada que ya no encajan: mejor sin dato que con uno falso


def _seconds_left(clocks_json: list | None, ply: int) -> float | None:
    """Reloj de quien acaba de jugar, tras su jugada (RF-1.2).

    `clocks_json` es la lista plana de chess.com: un valor por media jugada, en
    el mismo orden en que se jugaron, así que el índice es el ply.
    """
    if not clocks_json or ply >= len(clocks_json):
        return None
    seconds_left = clocks_json[ply]
    return float(seconds_left) if seconds_left is not None else None


def analysis_critical_moments(
    moves: Sequence[AnalyzedMove], cached_alternatives: dict[int, list[dict]]
) -> list[CriticalMoment]:
    """Los momentos críticos de una partida analizada (RF-2.8).

    Aquí entran las jugadas de **los dos** bandos, al revés que en los patrones
    del jugador: en el visor se recorre la partida entera, y una posición donde
    el rival tenía una sola jugada es tan interesante de ver como una propia.

    `cached_alternatives` es lo que `alternatives_from_cache` haya podido
    rescatar para un análisis anterior a RF-10; sin alternativas no se puede
    afirmar que una jugada fuera única, así que esos análisis salen con menos
    momentos, no con momentos inventados.
    """
    return critical_moments(
        [
            # El reloj no decide si una posición es crítica, así que no hace falta.
            _move_context(move, None, alternatives_of(move, cached_alternatives))
            for move in moves
        ]
    )

"""Estadísticas agregadas sobre las partidas y sus análisis (RF-3).

Nada de esto lanza un motor: todo sale de lo que ya está guardado. Lo que se
puede contar en SQL se agrega aquí (marcador, ratings, partidas por mes,
precisión y reparto por fases); lo que hay que leer jugada a jugada —tipo de
error, tramos de reloj y evaluación al salir de la apertura— se lo pide a
`lucia_core.insights` a través de `services/insights.py`, y las reglas viven
allí, no aquí.

Una partida sin analizar cuenta para resultados y ratings (RF-3.1) pero no
para lo demás, que necesita un `Analysis` terminado. Y una analizada con los
dos motores (RF-2.6) cuenta **una sola vez**, con su análisis más reciente
(`latest_analysis_ids`): sumar las dos filas contaba dos veces la misma
partida y torcía la precisión media, el número de partidas analizadas y el
reparto por fases.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lucia_core.insights import (
    MistakeTypeCount,
    MoveContext,
    TimeBucketStats,
    is_time_trouble,
    mistakes_by_type,
    opening_exit_win_percent,
    time_pressure,
)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.services.games import is_player, outcome_of, player_color, player_side
from lucia_api.services.insights import latest_analysis_ids, player_move_contexts


@dataclass
class RecordSummary:
    """Marcador de un jugador: victorias, tablas y derrotas."""

    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def total(self) -> int:
        return self.wins + self.draws + self.losses

    @property
    def score_percent(self) -> float:
        """Puntuación clásica: una victoria vale 1, unas tablas 0.5."""
        if self.total == 0:
            return 0.0
        return (self.wins + self.draws * 0.5) / self.total * 100


@dataclass
class TimeClassStats:
    time_class: str
    record: RecordSummary
    current_rating: int | None = None


@dataclass
class MonthlyCount:
    year: int
    month: int
    games: int


@dataclass
class OpeningStats:
    """Rendimiento por apertura (RF-3.2).

    El nombre y el código salen de la tabla ECO propia
    (`lucia_core.openings`), no de la URL que reporta chess.com: sale en más
    partidas, trae el código —que chess.com no da— y reconoce transposiciones.
    Las partidas que no empiezan en la posición estándar no tienen apertura y
    no aparecen aquí.
    """

    opening: str
    eco: str | None
    color: str
    record: RecordSummary
    average_accuracy: float | None = None
    average_opening_exit_win_percent: float | None = None
    """Con qué posición se sale de la apertura, en probabilidad de victoria del
    jugador (RF-3.2): la media de la evaluación tras su última jugada de fase
    `opening` en cada partida. `None` si ninguna de esas partidas está
    analizada."""


@dataclass
class PhaseStats:
    """Cuánta probabilidad de victoria se pierde en cada fase (RF-3.3)."""

    phase: str
    moves: int
    average_accuracy: float
    average_win_percent_lost: float
    blunders: int


@dataclass
class TimeTroubleSummary:
    """Cuánto se juega con el reloj encima (RF-3.5)."""

    games_in_time_trouble: int
    """Partidas analizadas en las que se llegó a jugar con apuros."""
    analyzed_games_with_clocks: int
    """Sobre cuántas se puede decir: las que traen relojes de chess.com."""

    @property
    def share_of_games(self) -> float:
        if self.analyzed_games_with_clocks == 0:
            return 0.0
        return self.games_in_time_trouble / self.analyzed_games_with_clocks * 100


@dataclass
class PlayerStats:
    username: str
    total_games: int
    overall: RecordSummary
    by_time_class: list[TimeClassStats] = field(default_factory=list)
    by_month: list[MonthlyCount] = field(default_factory=list)
    by_opening: list[OpeningStats] = field(default_factory=list)
    by_phase: list[PhaseStats] = field(default_factory=list)
    by_mistake_type: list[MistakeTypeCount] = field(default_factory=list)
    """Por qué se falla, no solo cuánto (RF-3.4)."""
    by_time_left: list[TimeBucketStats] = field(default_factory=list)
    """Cómo cae la calidad de juego según baja el reloj (RF-3.5)."""
    time_trouble: TimeTroubleSummary | None = None
    analyzed_games: int = 0
    average_accuracy: float | None = None


async def get_player_stats(
    session: AsyncSession, username: str, limit_openings: int = 10
) -> PlayerStats:
    outcome = outcome_of(username)

    # --- Resultados globales y por control de tiempo (RF-3.1) ---
    outcome_rows = (
        await session.execute(
            select(Game.time_class, outcome.label("outcome"), func.count())
            .where(is_player(username))
            .group_by(Game.time_class, "outcome")
        )
    ).all()

    overall = RecordSummary()
    by_time_class: dict[str, RecordSummary] = {}
    for time_class, player_outcome, game_count in outcome_rows:
        record = by_time_class.setdefault(time_class, RecordSummary())
        _add(record, player_outcome, game_count)
        _add(overall, player_outcome, game_count)

    # Rating actual por control: el de la partida más reciente de cada tipo.
    ratings = await _current_ratings(session, username)

    # --- Partidas por mes (RF-3.1) ---
    monthly_rows = (
        await session.execute(
            select(Game.year, Game.month, func.count())
            .where(is_player(username))
            .group_by(Game.year, Game.month)
            .order_by(Game.year, Game.month)
        )
    ).all()

    # --- Precisión media y partidas analizadas ---
    analyzed_games, average_accuracy = await _accuracy_summary(session, username)

    # --- Patrones (RF-2.8, RF-3.4, RF-3.5) ---
    # Las jugadas del jugador se cargan una sola vez: los tres extractores
    # miran el mismo material desde ángulos distintos.
    move_contexts = await player_move_contexts(session, username)
    moves = [context for _game_id, context in move_contexts]

    return PlayerStats(
        username=username,
        total_games=overall.total,
        overall=overall,
        by_time_class=[
            TimeClassStats(
                time_class=time_class, record=record, current_rating=ratings.get(time_class)
            )
            for time_class, record in sorted(by_time_class.items())
        ],
        by_month=[
            MonthlyCount(year=year, month=month, games=games) for year, month, games in monthly_rows
        ],
        by_opening=await _opening_stats(session, username, limit_openings, move_contexts),
        by_phase=await _phase_stats(session, username),
        by_mistake_type=mistakes_by_type(moves),
        by_time_left=time_pressure(moves),
        time_trouble=_time_trouble_summary(move_contexts),
        analyzed_games=analyzed_games,
        average_accuracy=average_accuracy,
    )


def _time_trouble_summary(
    move_contexts: list[tuple[int, MoveContext]],
) -> TimeTroubleSummary:
    """En cuántas partidas se llegó a jugar con apuros (RF-3.5).

    Se cuenta por partidas y no por jugadas porque la pregunta es de hábito:
    "me pasa a menudo" es una respuesta distinta de "un día me pasó veinte
    veces seguidas".
    """
    games_with_clocks = {
        game_id for game_id, move in move_contexts if move.seconds_left is not None
    }
    games_in_trouble = {
        game_id for game_id, move in move_contexts if is_time_trouble(move.seconds_left)
    }
    return TimeTroubleSummary(
        games_in_time_trouble=len(games_in_trouble),
        analyzed_games_with_clocks=len(games_with_clocks),
    )


def _add(record: RecordSummary, outcome: str, game_count: int) -> None:
    if outcome == "win":
        record.wins += game_count
    elif outcome == "draw":
        record.draws += game_count
    else:
        record.losses += game_count


async def _current_ratings(session: AsyncSession, username: str) -> dict[str, int]:
    """Rating por control de tiempo, tomado de la partida más reciente."""
    player_rating = player_side(username, Game.white_rating, Game.black_rating)
    rating_rows = (
        await session.execute(
            select(Game.time_class, player_rating, Game.played_at)
            .where(is_player(username))
            .order_by(Game.played_at.desc())
        )
    ).all()

    ratings: dict[str, int] = {}
    for time_class, rating, _played_at in rating_rows:
        ratings.setdefault(time_class, rating)  # la primera es la más reciente
    return ratings


async def _accuracy_summary(session: AsyncSession, username: str) -> tuple[int, float | None]:
    """Cuántas partidas tienen análisis terminado y la precisión media del
    usuario en ellas.

    Una partida analizada con los dos motores (RF-2.6) cuenta una sola vez: se
    toma su análisis más reciente, igual que en el reparto por fases y en los
    patrones, o la misma partida contaría dos veces y la media saldría torcida.
    """
    player_accuracy = player_side(username, Analysis.white_accuracy, Analysis.black_accuracy)
    accuracy_row = (
        await session.execute(
            select(func.count(), func.avg(player_accuracy))
            .select_from(Analysis)
            .join(Game, Analysis.game_id == Game.id)
            .where(is_player(username), Analysis.id.in_(latest_analysis_ids()))
        )
    ).one()
    analyzed_games, average_accuracy = accuracy_row
    return analyzed_games, float(average_accuracy) if average_accuracy is not None else None


async def _opening_stats(
    session: AsyncSession,
    username: str,
    limit: int,
    move_contexts: list[tuple[int, MoveContext]],
) -> list[OpeningStats]:
    color = player_color(username)
    outcome = outcome_of(username)

    opening_rows = (
        await session.execute(
            select(
                Game.opening_name,
                Game.opening_eco,
                color.label("color"),
                outcome.label("outcome"),
                func.count(),
            )
            .where(is_player(username), Game.opening_name.is_not(None))
            .group_by(Game.opening_name, Game.opening_eco, "color", "outcome")
        )
    ).all()

    eco_by_opening: dict[str, str | None] = {}
    records_by_opening: dict[tuple[str, str], RecordSummary] = {}
    for opening_name, eco, played_color, player_outcome, game_count in opening_rows:
        eco_by_opening[opening_name] = eco
        opening_key = (opening_name, played_color)
        _add(
            records_by_opening.setdefault(opening_key, RecordSummary()), player_outcome, game_count
        )

    accuracy_by_opening = await _accuracy_by_opening(session, username)
    exit_by_opening = await _opening_exit_by_opening(session, username, move_contexts)
    sorted_openings = sorted(
        records_by_opening.items(), key=lambda item: item[1].total, reverse=True
    )
    return [
        OpeningStats(
            opening=opening_name,
            eco=eco_by_opening.get(opening_name),
            color=played_color,
            record=record,
            average_accuracy=accuracy_by_opening.get((opening_name, played_color)),
            average_opening_exit_win_percent=exit_by_opening.get((opening_name, played_color)),
        )
        for (opening_name, played_color), record in sorted_openings[:limit]
    ]


async def _accuracy_by_opening(
    session: AsyncSession, username: str
) -> dict[tuple[str, str], float]:
    """Precisión media del usuario en cada apertura, solo con las partidas que
    ya tienen análisis terminado."""
    color = player_color(username)
    player_accuracy = player_side(username, Analysis.white_accuracy, Analysis.black_accuracy)
    accuracy_rows = (
        await session.execute(
            select(Game.opening_name, color.label("color"), func.avg(player_accuracy))
            .select_from(Analysis)
            .join(Game, Analysis.game_id == Game.id)
            .where(
                is_player(username),
                Analysis.id.in_(latest_analysis_ids()),
                Game.opening_name.is_not(None),
            )
            .group_by(Game.opening_name, "color")
        )
    ).all()
    return {
        (opening_name, played_color): float(average_accuracy)
        for opening_name, played_color, average_accuracy in accuracy_rows
        if average_accuracy is not None
    }


async def _opening_exit_by_opening(
    session: AsyncSession, username: str, move_contexts: list[tuple[int, MoveContext]]
) -> dict[tuple[str, str], float]:
    """Evaluación media al salir de la apertura, por apertura y color (RF-3.2).

    La saca `lucia_core.insights.opening_exit_win_percent` partida a partida; lo
    que hace falta aquí es saber a qué apertura pertenece cada una.
    """
    opening_rows = (
        await session.execute(
            select(Game.id, Game.opening_name, player_color(username)).where(
                is_player(username), Game.opening_name.is_not(None)
            )
        )
    ).all()
    opening_by_game = {
        game_id: (opening_name, played_color)
        for game_id, opening_name, played_color in opening_rows
    }

    moves_by_game: dict[int, list[MoveContext]] = {}
    for game_id, move in move_contexts:
        moves_by_game.setdefault(game_id, []).append(move)

    exits_by_opening: dict[tuple[str, str], list[float]] = {}
    for game_id, game_moves in moves_by_game.items():
        opening_key = opening_by_game.get(game_id)
        exit_win_percent = opening_exit_win_percent(game_moves)
        if opening_key is None or exit_win_percent is None:
            continue
        exits_by_opening.setdefault(opening_key, []).append(exit_win_percent)

    return {opening_key: sum(exits) / len(exits) for opening_key, exits in exits_by_opening.items()}


async def _phase_stats(session: AsyncSession, username: str) -> list[PhaseStats]:
    """Precisión y pérdida de probabilidad de victoria por fase (RF-3.3).

    Solo cuentan las jugadas *del usuario*: mezclar las del rival diría más
    sobre cómo juega el otro que sobre uno mismo.
    """
    color = player_color(username)
    win_percent_lost = AnalyzedMove.win_percent_before - AnalyzedMove.win_percent_after

    phase_rows = (
        await session.execute(
            select(
                AnalyzedMove.phase,
                func.count(),
                func.avg(AnalyzedMove.move_accuracy),
                func.avg(win_percent_lost),
                func.sum(case((AnalyzedMove.classification == "blunder", 1), else_=0)),
            )
            .select_from(AnalyzedMove)
            .join(Analysis, AnalyzedMove.analysis_id == Analysis.id)
            .join(Game, Analysis.game_id == Game.id)
            .where(
                is_player(username),
                Analysis.id.in_(latest_analysis_ids()),
                AnalyzedMove.color == color,
            )
            .group_by(AnalyzedMove.phase)
        )
    ).all()

    phase_order = {"opening": 0, "middlegame": 1, "endgame": 2}
    phase_stats = [
        PhaseStats(
            phase=phase,
            moves=moves,
            average_accuracy=float(accuracy or 0),
            average_win_percent_lost=float(average_win_percent_lost or 0),
            blunders=int(blunders or 0),
        )
        for phase, moves, accuracy, average_win_percent_lost, blunders in phase_rows
    ]
    return sorted(phase_stats, key=lambda p: phase_order.get(p.phase, 99))

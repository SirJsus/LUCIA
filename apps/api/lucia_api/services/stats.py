"""Estadísticas agregadas sobre las partidas y sus análisis (RF-3).

Nada de esto lanza un motor: todo sale de lo que ya está guardado. Lo que se
puede contar en SQL se agrega aquí (marcador, ratings, partidas por mes,
precisión y reparto por fases); lo que hay que leer jugada a jugada —tipo de
error, tramos de reloj y evaluación al salir de la apertura— se lo pide a
`lucia_core.insights` a través de `services/insights.py`, y las reglas viven
allí, no aquí. Lo consume `routers/stats.py`, que solo traduce estos
`dataclass` a los modelos de respuesta de `GET /stats/{username}`.

La excepción a ese reparto son las tendencias (RF-3.7): el núcleo compara
tramos de jugadas sin saber de qué tamaño son, así que **el tramo se decide
aquí** —mes natural, el mismo con el que se cuentan las partidas en RF-3.1—
y aquí se le pega a cada mes el rating con el que se cerró, que es un dato de
`games` y no del análisis.

Aquí solo hay partidas: los tableros de análisis no entran (RF-6.5) y sus
análisis los descarta `latest_analysis_ids`. Un tablero marcado como "partida
propia" sí cuenta, pero tampoco hace falta mirarlo: al marcarlo se publica
como una fila más de `games` y llega a estas consultas como cualquier otra
partida, sin que ninguna de ellas cambie (ADR-0014). Sale bajo el control de
tiempo "sin determinar", como las importadas de un PGN, así que no entra en la
línea de rating de las tendencias (`_most_played_time_class` descarta
`"unknown"`).

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
    MoveQuality,
    TimeBucketStats,
    TrendChange,
    is_time_trouble,
    mistakes_by_type,
    move_quality,
    opening_exit_win_percent,
    time_pressure,
    trend_change,
)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.services.games import (
    UNKNOWN_TIME_CLASS,
    is_player,
    outcome_of,
    player_color,
    player_side,
)
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
class MonthlyQuality:
    """Cómo se jugó en un mes concreto (RF-3.7)."""

    year: int
    month: int
    analyzed_games: int
    quality: MoveQuality
    rating: int | None = None
    """Rating con el que se cerró el mes en el control de tiempo más jugado
    (`TrendsSummary.rating_time_class`). `None` si ese mes no se jugó ninguna partida
    de ese control."""


@dataclass
class TrendsSummary:
    """Evolución del juego en el tiempo (RF-3.7).

    Solo entran los meses con **alguna partida analizada**: la precisión y el
    tipo de error salen del análisis, y un mes jugado pero sin analizar
    aparecería como un cero que se lee como un desastre.
    """

    by_month: list[MonthlyQuality] = field(default_factory=list)
    change: TrendChange | None = None
    rating_time_class: str | None = None
    """A qué control de tiempo pertenece la línea de rating: el más jugado.
    Mezclar bullet y rapid en una sola serie haría que un mes de más bullet
    pareciera una caída de rating, cuando son dos escalas distintas."""


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
    trends: TrendsSummary = field(default_factory=TrendsSummary)
    """Evolución de precisión y tipo de errores mes a mes (RF-3.7)."""
    analyzed_games: int = 0
    average_accuracy: float | None = None


#: Cuántas aperturas se miran cuando lo que se busca es la que cuesta puntos:
#: las más jugadas, que es como las devuelve RF-3.2, y de ellas las que pierden
#: puntos. Lo preguntan igual el plan semanal (RF-4.5) y el drill de aperturas
#: (RF-4.2), así que el número es uno solo y vive junto a quien lo responde.
MAX_OPENINGS_CONSIDERED = 40


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

    time_class_stats = [
        TimeClassStats(time_class=time_class, record=record, current_rating=ratings.get(time_class))
        for time_class, record in sorted(by_time_class.items())
    ]

    return PlayerStats(
        username=username,
        total_games=overall.total,
        overall=overall,
        by_time_class=time_class_stats,
        by_month=[
            MonthlyCount(year=year, month=month, games=games) for year, month, games in monthly_rows
        ],
        by_opening=await _opening_stats(session, username, limit_openings, move_contexts),
        by_phase=await _phase_stats(session, username),
        by_mistake_type=mistakes_by_type(moves),
        by_time_left=time_pressure(moves),
        time_trouble=_time_trouble_summary(move_contexts),
        trends=await _trends_summary(session, username, move_contexts, time_class_stats),
        analyzed_games=analyzed_games,
        average_accuracy=average_accuracy,
    )


async def _trends_summary(
    session: AsyncSession,
    username: str,
    move_contexts: list[tuple[int, MoveContext]],
    time_class_stats: list[TimeClassStats],
) -> TrendsSummary:
    """Evolución mes a mes de la precisión y del tipo de errores (RF-3.7).

    El tramo es el **mes natural**, el mismo con el que ya se cuentan las
    partidas en RF-3.1, para que las dos series se lean sobre el mismo eje. La
    calidad de cada mes la resume `lucia_core.insights.move_quality` —la regla
    de qué es un error y de qué tipo es la misma que la de RF-3.4—; aquí solo
    se reparten las jugadas por mes y se les pega el rating de cierre.

    El rating del mes es el de la **última** partida del mes en
    `rating_time_class`, no la media: el rating es un estado, no una magnitud
    que se promedie, y así la serie coincide con el "Rating" que la tabla de
    RF-3.1 enseña para el mes en curso.
    """
    rating_time_class = _most_played_time_class(time_class_stats)
    game_rows = (
        await session.execute(
            select(
                Game.id,
                Game.year,
                Game.month,
                Game.time_class,
                player_side(username, Game.white_rating, Game.black_rating),
            )
            .where(is_player(username))
            .order_by(Game.played_at)
        )
    ).all()

    month_by_game: dict[int, tuple[int, int]] = {}
    ratings_by_month: dict[tuple[int, int], int] = {}
    for game_id, year, month, time_class, rating in game_rows:
        month_by_game[game_id] = (year, month)
        if time_class == rating_time_class and rating:
            # De más antigua a más reciente: la última partida del mes gana.
            ratings_by_month[(year, month)] = rating

    moves_by_month: dict[tuple[int, int], list[MoveContext]] = {}
    games_by_month: dict[tuple[int, int], set[int]] = {}
    for game_id, move in move_contexts:
        month = month_by_game[game_id]
        moves_by_month.setdefault(month, []).append(move)
        games_by_month.setdefault(month, set()).add(game_id)

    by_month = [
        MonthlyQuality(
            year=year,
            month=month,
            analyzed_games=len(games_by_month[(year, month)]),
            quality=quality,
            rating=ratings_by_month.get((year, month)),
        )
        for (year, month) in sorted(moves_by_month)
        if (quality := move_quality(moves_by_month[(year, month)])) is not None
    ]
    return TrendsSummary(
        by_month=by_month,
        change=trend_change([item.quality for item in by_month]),
        rating_time_class=rating_time_class if by_month else None,
    )


def _most_played_time_class(time_class_stats: list[TimeClassStats]) -> str | None:
    """El control de tiempo con más partidas, que es el de la línea de rating,
    o `None` si no hay ninguno del que se pueda hablar.

    Se elige uno y se dice cuál en vez de promediar todos: un mes de mucho
    bullet bajaría una media que mezclara escalas y parecería una caída de
    rating que no ocurrió.
    """
    # Las partidas sin ritmo conocido (RF-1.5, RF-6.5) quedan fuera de la
    # serie de rating: tampoco traen `WhiteElo`, así que la línea saldría
    # vacía y con un hueco por nombre.
    known = [item for item in time_class_stats if item.time_class != UNKNOWN_TIME_CLASS]
    if not known:
        return None
    return max(known, key=lambda item: item.record.total).time_class


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

"""Estadísticas agregadas sobre las partidas y sus análisis (RF-3).

Todo se calcula con SQL sobre lo que ya está guardado: no se lanza ningún
motor aquí. Una partida sin analizar cuenta para resultados y ratings
(RF-3.1) pero no para precisión ni fases (RF-3.2 / RF-3.3), que necesitan un
`Analysis` terminado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, AnalyzedMove, Game

#: Valores de `white_result`/`black_result` de chess.com que significan tablas.
DRAW_RESULTS = (
    "agreed",
    "repetition",
    "stalemate",
    "insufficient",
    "50move",
    "timevsinsufficient",
)


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

    El nombre sale de la URL de apertura que reporta chess.com (`games.eco`);
    la clasificación ECO propia llegará con `lucia_core.openings`. Falta de
    RF-3.2 la "eval promedio al salir de la apertura": necesita localizar la
    última jugada de fase `opening` de cada partida, y se hará junto con los
    extractores de patrones (RF-3.4, fase 2).
    """

    opening: str
    color: str
    record: RecordSummary
    average_accuracy: float | None = None


@dataclass
class PhaseStats:
    """Cuánta probabilidad de victoria se pierde en cada fase (RF-3.3)."""

    phase: str
    moves: int
    average_accuracy: float
    average_win_percent_lost: float
    blunders: int


@dataclass
class PlayerStats:
    username: str
    total_games: int
    overall: RecordSummary
    by_time_class: list[TimeClassStats] = field(default_factory=list)
    by_month: list[MonthlyCount] = field(default_factory=list)
    by_opening: list[OpeningStats] = field(default_factory=list)
    by_phase: list[PhaseStats] = field(default_factory=list)
    analyzed_games: int = 0
    average_accuracy: float | None = None


def _is_white(username: str):
    """Comparación insensible a mayúsculas.

    chess.com devuelve el perfil con el nombre canónico en minúsculas
    (`sirjsus`) pero dentro del PGN aparece como lo escribió el jugador
    (`SirJsus`). Comparando tal cual, buscar por el nombre del perfil no
    encontraría ninguna de sus propias partidas.
    """
    return func.lower(Game.white_username) == username.lower()


def _is_black(username: str):
    return func.lower(Game.black_username) == username.lower()


def _outcome_for(username: str):
    """Expresión SQL que traduce el resultado de la partida al del jugador.

    chess.com guarda el resultado por bando ("win", "checkmated"...), así que
    hay que mirar de qué color jugó el usuario en cada partida.
    """
    player_result = case(
        (_is_white(username), Game.white_result),
        else_=Game.black_result,
    )
    return case(
        (player_result == "win", "win"),
        (player_result.in_(DRAW_RESULTS), "draw"),
        else_="loss",
    )


def _is_player(username: str):
    return _is_white(username) | _is_black(username)


async def get_player_stats(
    session: AsyncSession, username: str, limit_openings: int = 10
) -> PlayerStats:
    outcome = _outcome_for(username)

    # --- Resultados globales y por control de tiempo (RF-3.1) ---
    outcome_rows = (
        await session.execute(
            select(Game.time_class, outcome.label("outcome"), func.count())
            .where(_is_player(username))
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
            .where(_is_player(username))
            .group_by(Game.year, Game.month)
            .order_by(Game.year, Game.month)
        )
    ).all()

    # --- Precisión media y partidas analizadas ---
    analyzed_games, average_accuracy = await _accuracy_summary(session, username)

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
        by_opening=await _opening_stats(session, username, limit_openings),
        by_phase=await _phase_stats(session, username),
        analyzed_games=analyzed_games,
        average_accuracy=average_accuracy,
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
    player_rating = case((_is_white(username), Game.white_rating), else_=Game.black_rating)
    rating_rows = (
        await session.execute(
            select(Game.time_class, player_rating, Game.played_at)
            .where(_is_player(username))
            .order_by(Game.played_at.desc())
        )
    ).all()

    ratings: dict[str, int] = {}
    for time_class, rating, _played_at in rating_rows:
        ratings.setdefault(time_class, rating)  # la primera es la más reciente
    return ratings


async def _accuracy_summary(session: AsyncSession, username: str) -> tuple[int, float | None]:
    """Cuántas partidas tienen análisis terminado y la precisión media del
    usuario en ellas."""
    player_accuracy = case(
        (_is_white(username), Analysis.white_accuracy),
        else_=Analysis.black_accuracy,
    )
    accuracy_row = (
        await session.execute(
            select(func.count(), func.avg(player_accuracy))
            .select_from(Analysis)
            .join(Game, Analysis.game_id == Game.id)
            .where(_is_player(username), Analysis.status == "done")
        )
    ).one()
    analyzed_games, average_accuracy = accuracy_row
    return analyzed_games, float(average_accuracy) if average_accuracy is not None else None


async def _opening_stats(session: AsyncSession, username: str, limit: int) -> list[OpeningStats]:
    color = case((_is_white(username), "white"), else_="black")
    outcome = _outcome_for(username)

    opening_rows = (
        await session.execute(
            select(Game.eco, color.label("color"), outcome.label("outcome"), func.count())
            .where(_is_player(username), Game.eco.is_not(None))
            .group_by(Game.eco, "color", "outcome")
        )
    ).all()

    records_by_opening: dict[tuple[str, str], RecordSummary] = {}
    for eco, played_color, player_outcome, game_count in opening_rows:
        opening_key = (_opening_name(eco), played_color)
        _add(
            records_by_opening.setdefault(opening_key, RecordSummary()), player_outcome, game_count
        )

    accuracy_by_opening = await _accuracy_by_opening(session, username)
    sorted_openings = sorted(
        records_by_opening.items(), key=lambda item: item[1].total, reverse=True
    )
    return [
        OpeningStats(
            opening=opening_name,
            color=played_color,
            record=record,
            average_accuracy=accuracy_by_opening.get((opening_name, played_color)),
        )
        for (opening_name, played_color), record in sorted_openings[:limit]
    ]


async def _accuracy_by_opening(
    session: AsyncSession, username: str
) -> dict[tuple[str, str], float]:
    """Precisión media del usuario en cada apertura, solo con las partidas que
    ya tienen análisis terminado."""
    color = case((_is_white(username), "white"), else_="black")
    player_accuracy = case(
        (_is_white(username), Analysis.white_accuracy),
        else_=Analysis.black_accuracy,
    )
    accuracy_rows = (
        await session.execute(
            select(Game.eco, color.label("color"), func.avg(player_accuracy))
            .select_from(Analysis)
            .join(Game, Analysis.game_id == Game.id)
            .where(_is_player(username), Analysis.status == "done", Game.eco.is_not(None))
            .group_by(Game.eco, "color")
        )
    ).all()
    return {
        (_opening_name(eco), played_color): float(average_accuracy)
        for eco, played_color, average_accuracy in accuracy_rows
        if average_accuracy is not None
    }


def _opening_name(eco_url: str) -> str:
    """chess.com da la apertura como URL
    (`https://www.chess.com/openings/Italian-Game-2.Nf3`); aquí solo se
    extrae el nombre legible."""
    name = eco_url.rstrip("/").rsplit("/", 1)[-1]
    return name.replace("-", " ")


async def _phase_stats(session: AsyncSession, username: str) -> list[PhaseStats]:
    """Precisión y pérdida de probabilidad de victoria por fase (RF-3.3).

    Solo cuentan las jugadas *del usuario*: mezclar las del rival diría más
    sobre cómo juega el otro que sobre uno mismo.
    """
    player_color = case((_is_white(username), "white"), else_="black")
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
                _is_player(username),
                Analysis.status == "done",
                AnalyzedMove.color == player_color,
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

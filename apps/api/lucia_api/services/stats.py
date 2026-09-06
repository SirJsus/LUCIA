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


def _es_blancas(username: str):
    """Comparación insensible a mayúsculas.

    chess.com devuelve el perfil con el nombre canónico en minúsculas
    (`sirjsus`) pero dentro del PGN aparece como lo escribió el jugador
    (`SirJsus`). Comparando tal cual, buscar por el nombre del perfil no
    encontraría ninguna de sus propias partidas.
    """
    return func.lower(Game.white_username) == username.lower()


def _es_negras(username: str):
    return func.lower(Game.black_username) == username.lower()


def _outcome_for(username: str):
    """Expresión SQL que traduce el resultado de la partida al del jugador.

    chess.com guarda el resultado por bando ("win", "checkmated"...), así que
    hay que mirar de qué color jugó el usuario en cada partida.
    """
    resultado_del_jugador = case(
        (_es_blancas(username), Game.white_result),
        else_=Game.black_result,
    )
    return case(
        (resultado_del_jugador == "win", "win"),
        (resultado_del_jugador.in_(DRAW_RESULTS), "draw"),
        else_="loss",
    )


def _is_player(username: str):
    return _es_blancas(username) | _es_negras(username)


async def get_player_stats(
    session: AsyncSession, username: str, limit_openings: int = 10
) -> PlayerStats:
    outcome = _outcome_for(username)

    # --- Resultados globales y por control de tiempo (RF-3.1) ---
    filas = (
        await session.execute(
            select(Game.time_class, outcome.label("outcome"), func.count())
            .where(_is_player(username))
            .group_by(Game.time_class, "outcome")
        )
    ).all()

    overall = RecordSummary()
    por_control: dict[str, RecordSummary] = {}
    for time_class, resultado, cuantas in filas:
        registro = por_control.setdefault(time_class, RecordSummary())
        _add(registro, resultado, cuantas)
        _add(overall, resultado, cuantas)

    # Rating actual por control: el de la partida más reciente de cada tipo.
    ratings = await _current_ratings(session, username)

    # --- Partidas por mes (RF-3.1) ---
    meses = (
        await session.execute(
            select(Game.year, Game.month, func.count())
            .where(_is_player(username))
            .group_by(Game.year, Game.month)
            .order_by(Game.year, Game.month)
        )
    ).all()

    # --- Precisión media y partidas analizadas ---
    analizadas, precision_media = await _accuracy_summary(session, username)

    return PlayerStats(
        username=username,
        total_games=overall.total,
        overall=overall,
        by_time_class=[
            TimeClassStats(
                time_class=time_class, record=registro, current_rating=ratings.get(time_class)
            )
            for time_class, registro in sorted(por_control.items())
        ],
        by_month=[MonthlyCount(year=y, month=m, games=c) for y, m, c in meses],
        by_opening=await _opening_stats(session, username, limit_openings),
        by_phase=await _phase_stats(session, username),
        analyzed_games=analizadas,
        average_accuracy=precision_media,
    )


def _add(registro: RecordSummary, resultado: str, cuantas: int) -> None:
    if resultado == "win":
        registro.wins += cuantas
    elif resultado == "draw":
        registro.draws += cuantas
    else:
        registro.losses += cuantas


async def _current_ratings(session: AsyncSession, username: str) -> dict[str, int]:
    """Rating por control de tiempo, tomado de la partida más reciente."""
    rating_del_jugador = case((_es_blancas(username), Game.white_rating), else_=Game.black_rating)
    filas = (
        await session.execute(
            select(Game.time_class, rating_del_jugador, Game.played_at)
            .where(_is_player(username))
            .order_by(Game.played_at.desc())
        )
    ).all()

    ratings: dict[str, int] = {}
    for time_class, rating, _played_at in filas:
        ratings.setdefault(time_class, rating)  # la primera es la más reciente
    return ratings


async def _accuracy_summary(session: AsyncSession, username: str) -> tuple[int, float | None]:
    """Cuántas partidas tienen análisis terminado y la precisión media del
    usuario en ellas."""
    precision_del_jugador = case(
        (_es_blancas(username), Analysis.white_accuracy),
        else_=Analysis.black_accuracy,
    )
    fila = (
        await session.execute(
            select(func.count(), func.avg(precision_del_jugador))
            .select_from(Analysis)
            .join(Game, Analysis.game_id == Game.id)
            .where(_is_player(username), Analysis.status == "done")
        )
    ).one()
    cuantas, media = fila
    return cuantas, float(media) if media is not None else None


async def _opening_stats(session: AsyncSession, username: str, limite: int) -> list[OpeningStats]:
    color = case((_es_blancas(username), "white"), else_="black")
    outcome = _outcome_for(username)

    filas = (
        await session.execute(
            select(Game.eco, color.label("color"), outcome.label("outcome"), func.count())
            .where(_is_player(username), Game.eco.is_not(None))
            .group_by(Game.eco, "color", "outcome")
        )
    ).all()

    agrupadas: dict[tuple[str, str], RecordSummary] = {}
    for eco, color_jugado, resultado, cuantas in filas:
        clave = (_opening_name(eco), color_jugado)
        _add(agrupadas.setdefault(clave, RecordSummary()), resultado, cuantas)

    precisiones = await _accuracy_by_opening(session, username)
    ordenadas = sorted(agrupadas.items(), key=lambda item: item[1].total, reverse=True)
    return [
        OpeningStats(
            opening=nombre,
            color=color_jugado,
            record=registro,
            average_accuracy=precisiones.get((nombre, color_jugado)),
        )
        for (nombre, color_jugado), registro in ordenadas[:limite]
    ]


async def _accuracy_by_opening(
    session: AsyncSession, username: str
) -> dict[tuple[str, str], float]:
    """Precisión media del usuario en cada apertura, solo con las partidas que
    ya tienen análisis terminado."""
    color = case((_es_blancas(username), "white"), else_="black")
    precision_del_jugador = case(
        (_es_blancas(username), Analysis.white_accuracy),
        else_=Analysis.black_accuracy,
    )
    filas = (
        await session.execute(
            select(Game.eco, color.label("color"), func.avg(precision_del_jugador))
            .select_from(Analysis)
            .join(Game, Analysis.game_id == Game.id)
            .where(_is_player(username), Analysis.status == "done", Game.eco.is_not(None))
            .group_by(Game.eco, "color")
        )
    ).all()
    return {
        (_opening_name(eco), color_jugado): float(media)
        for eco, color_jugado, media in filas
        if media is not None
    }


def _opening_name(eco_url: str) -> str:
    """chess.com da la apertura como URL
    (`https://www.chess.com/openings/Italian-Game-2.Nf3`); aquí solo se
    extrae el nombre legible."""
    nombre = eco_url.rstrip("/").rsplit("/", 1)[-1]
    return nombre.replace("-", " ")


async def _phase_stats(session: AsyncSession, username: str) -> list[PhaseStats]:
    """Precisión y pérdida de probabilidad de victoria por fase (RF-3.3).

    Solo cuentan las jugadas *del usuario*: mezclar las del rival diría más
    sobre cómo juega el otro que sobre uno mismo.
    """
    color_del_jugador = case((_es_blancas(username), "white"), else_="black")
    perdida = AnalyzedMove.win_percent_before - AnalyzedMove.win_percent_after

    filas = (
        await session.execute(
            select(
                AnalyzedMove.phase,
                func.count(),
                func.avg(AnalyzedMove.move_accuracy),
                func.avg(perdida),
                func.sum(case((AnalyzedMove.classification == "blunder", 1), else_=0)),
            )
            .select_from(AnalyzedMove)
            .join(Analysis, AnalyzedMove.analysis_id == Analysis.id)
            .join(Game, Analysis.game_id == Game.id)
            .where(
                _is_player(username),
                Analysis.status == "done",
                AnalyzedMove.color == color_del_jugador,
            )
            .group_by(AnalyzedMove.phase)
        )
    ).all()

    orden = {"opening": 0, "middlegame": 1, "endgame": 2}
    resultado = [
        PhaseStats(
            phase=fase,
            moves=jugadas,
            average_accuracy=float(precision or 0),
            average_win_percent_lost=float(perdida_media or 0),
            blunders=int(blunders or 0),
        )
        for fase, jugadas, precision, perdida_media, blunders in filas
    ]
    return sorted(resultado, key=lambda p: orden.get(p.phase, 99))

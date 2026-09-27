"""Cómo se mira una partida desde el punto de vista de un jugador.

Una fila de `games` no dice quién ganó: dice qué le pasó a las blancas y qué a
las negras. Para responder "¿cuántas gané yo?" hay que saber de qué color jugó
el usuario en cada una, y eso son las mismas cuatro expresiones SQL en todas
partes: el listado con filtros (RF-5.3) y las estadísticas (RF-3).

Vive aquí, y no repetido en cada consulta, porque la comparación tiene una
trampa: chess.com devuelve el perfil con el nombre canónico en minúsculas
(`sirjsus`) pero dentro del PGN aparece como lo escribió el jugador
(`SirJsus`). Comparando tal cual, buscar por el nombre del perfil no
encontraría ninguna de sus propias partidas.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from lucia_core.openings import opening_of_pgn
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, Game

#: Estados de `Analysis.status` que significan "todavía no hay resultado": la
#: cola del worker (RF-2.4) los recorre en este orden. Los demás son "done" y
#: "error", que sí son finales.
ANALYSIS_UNFINISHED_STATUSES = ("queued", "running")

#: Valores de `white_result`/`black_result` que significan tablas: los de
#: chess.com, que dicen además cómo se llegó a ellas, más el "draw" a secas que
#: guarda el importador de PGN manual (RF-1.5), donde el archivo solo dice
#: "1/2-1/2" y no cómo acabó.
#: Cualquier otro valor distinto de "win" significa que ese bando perdió.
DRAW_RESULTS = (
    "draw",
    "agreed",
    "repetition",
    "stalemate",
    "insufficient",
    "50move",
    "timevsinsufficient",
)


#: Los huecos con los que se guarda el ritmo de una partida que no dice a qué
#: se jugó: las de un archivo PGN (RF-1.5) y las publicadas desde un tablero
#: (RF-6.5). Se dejan en hueco en vez de inventar una categoría, y por eso
#: `services/stats.py` los descarta de la línea de rating de las tendencias.
UNKNOWN_TIME_CONTROL = "-"
UNKNOWN_TIME_CLASS = "unknown"


def set_pgn_and_opening(game: Game, pgn: str) -> None:
    """Deja en la partida el PGN y la apertura que se deduce de él.

    Van juntos porque la apertura sale del PGN: guardar uno sin la otra
    dejaría la partida contada bajo la apertura de unas jugadas anteriores.
    Lo usan las dos vías que guardan un PGN propio: la importación manual
    (RF-1.5) y la publicación de un tablero como partida propia (RF-6.5).
    """
    game.pgn = pgn
    opening = opening_of_pgn(pgn)
    game.opening_eco = opening.eco if opening else None
    game.opening_name = opening.name if opening else None


def is_white(username: str):
    """La partida la jugó `username` con blancas."""
    return func.lower(Game.white_username) == username.lower()


def is_black(username: str):
    return func.lower(Game.black_username) == username.lower()


def is_player(username: str):
    """`username` jugó esa partida, del color que sea."""
    return is_white(username) | is_black(username)


def player_side(username: str, white_value, black_value):
    """El valor del lado con el que jugó `username`: `white_value` si jugó con
    blancas, `black_value` si con negras (su rating, su precisión, su
    resultado...)."""
    return case((is_white(username), white_value), else_=black_value)


def player_color(username: str):
    """Con qué color jugó `username`: "white" o "black"."""
    return player_side(username, "white", "black")


def outcome_of(username: str):
    """Expresión SQL con el resultado **de ese jugador**: "win", "draw" o
    "loss", mirando de qué color jugó."""
    player_result = player_side(username, Game.white_result, Game.black_result)
    return case(
        (player_result == "win", "win"),
        (player_result.in_(DRAW_RESULTS), "draw"),
        else_="loss",
    )


@dataclass(frozen=True)
class GameAnalysisState:
    """Qué análisis tiene ya una partida.

    Lo necesitan la lista de partidas (RF-5.3), para decir de un vistazo qué
    está analizado y con qué, y el análisis en lote (RF-2.5), para que quien
    elige la tanda no vuelva a mandar lo que ya está hecho.
    """

    analyzed_by_engines: tuple[str, ...]
    """Motores cuyo análisis terminó, en orden alfabético. Puede haber más de
    uno: una misma partida se analiza con Stockfish y con Lc0 como segunda
    opinión (RF-2.6), y son análisis distintos."""
    has_analysis_in_progress: bool
    """Hay un análisis suyo en la cola o corriendo (RF-2.4). Se enseña aparte
    de los terminados porque es lo que explica que una partida recién mandada
    todavía no tenga motor que mostrar."""


async def load_analysis_state_by_game_id(
    session: AsyncSession, game_ids: Sequence[int]
) -> dict[int, GameAnalysisState]:
    """El estado de análisis de cada partida pedida, sacado de `analyses`.

    **De dónde sale**: de la tabla de análisis, no de una columna de `games`.
    Una partida no "está analizada" como propiedad suya; tiene tantas corridas
    de motor como se le hayan lanzado, con motor y profundidad propios (ver
    `Analysis`). Por eso lo que vuelve no es un booleano sino con qué motores
    terminó.

    **Por qué en una sola consulta**: la lista sirve hasta 200 partidas de una
    vez, y preguntar por cada fila serían 200 idas y vueltas a la base para
    pintar una columna.

    Los análisis de tablero cuentan si están atribuidos a la partida
    (`game_id` lleno, RF-6.5 y ADR-0014): son la misma corrida de motor sobre
    las mismas jugadas.
    """
    if not game_ids:
        return {}

    rows = await session.execute(
        select(Analysis.game_id, Analysis.engine, Analysis.status).where(
            Analysis.game_id.in_(game_ids)
        )
    )
    engines_done_by_game: dict[int, set[str]] = defaultdict(set)
    games_in_progress: set[int] = set()
    for game_id, engine, status in rows:
        if status == "done":
            engines_done_by_game[game_id].add(engine)
        elif status in ANALYSIS_UNFINISHED_STATUSES:
            games_in_progress.add(game_id)

    return {
        game_id: GameAnalysisState(
            analyzed_by_engines=tuple(sorted(engines_done_by_game.get(game_id, ()))),
            has_analysis_in_progress=game_id in games_in_progress,
        )
        for game_id in game_ids
    }

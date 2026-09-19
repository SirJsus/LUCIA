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

from lucia_core.openings import opening_of_pgn
from sqlalchemy import case, func

from lucia_api.db.models import Game

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

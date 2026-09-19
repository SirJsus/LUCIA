"""Publicar un tablero de análisis en el historial como partida propia
(RF-6.5).

Un tablero no cuenta en las estadísticas ni en la detección de patrones
(RF-3): es un sitio para tantear, y contar tanteos torcería el dashboard. Lo
que RF-6.5 promete es la excepción: si el usuario dice "esta partida la jugué
yo" —una OTB, una de otro club, una de un torneo— tiene que contar como
cualquier otra.

**Cómo cuenta: publicándola.** Al marcarlo, el tablero se guarda además como
una fila de `games`, con la misma forma que deja la importación de PGN manual
(RF-1.5): plataforma propia, huecos donde no hay dato y apertura deducida de
las jugadas. A partir de ahí el marcador, la tabla por control de tiempo, las
partidas por mes, las aperturas, las fases, los tipos de error, las tendencias
y los filtros del listado lo cuentan **sin que ninguna de sus consultas tenga
que aprender qué es un tablero** (ADR-0014).

De dónde viene y adónde va cada dato:

- **Las jugadas** las manda el front en PGN (`tree.ts::toPgn`), igual que al
  pedir el análisis (RF-6.9): recorrer el árbol de variantes es cosa de
  chess.js. Aquí solo se le ponen las cabeceras y se guarda.
- **Quién jugó, con qué color, con qué resultado y qué día** los escribe el
  usuario al marcar: el tablero no los tiene y deducirlos sería inventarlos.
- **Rating, control de tiempo y "de competición"** se quedan en hueco —0,
  "unknown", `False`—, los mismos que deja RF-1.5 y por la misma razón: un
  tablero tampoco los sabe.
- **La apertura** se deduce de las jugadas con la tabla ECO propia
  (`lucia_core.openings`), como en cualquier partida.

**El análisis del tablero cuenta mientras siga siendo el del tablero.** Si el
tablero ya tenía análisis terminado (RF-6.9), se le pone también `game_id` y
entra en el dashboard por la puerta de siempre (`latest_analysis_ids`). En
cuanto el tablero se edita, lo analizado deja de coincidir con la línea
principal y el enlace se retira hasta que se vuelva a analizar: pegar la
clasificación de una jugada sobre otra distinta sería meter un dato falso en
las estadísticas.
"""

from __future__ import annotations

import datetime as dt
import io
from typing import Literal

import chess.pgn
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Analysis, Board, Game, Player
from lucia_api.services.games import (
    UNKNOWN_TIME_CLASS,
    UNKNOWN_TIME_CONTROL,
    set_pgn_and_opening,
)
from lucia_api.services.pgn_import import SIDE_RESULTS_BY_PGN_RESULT, get_or_create_player

#: Plataforma con la que se guardan las partidas publicadas desde un tablero.
#: Propia, y no "manual", para poder distinguirlas de las de un archivo PGN:
#: `platform_id` es el id del tablero, así que volver a marcar el mismo
#: tablero reescribe su fila en vez de duplicarla.
BOARD_PLATFORM = "board"

PlayerColor = Literal["white", "black"]
PlayerResult = Literal["win", "draw", "loss"]


class OwnGameDetails(BaseModel):
    """Lo que el usuario tiene que decir para que su tablero pueda contar.

    Es el mínimo con el que las agregaciones de RF-3 responden sin inventar
    nada: de qué color jugó (marcador, aperturas por color, fases), contra
    quién (filtro por rival), cómo acabó (marcador) y qué día (partidas por
    mes y tendencias).
    """

    player_color: PlayerColor
    """De qué color jugó el usuario. Se pregunta el color y no los dos
    nombres para que su bando no pueda quedar mal escrito: el nombre con el
    que se guarda es su `username` de LUCIA, que es por donde casan las
    estadísticas."""
    opponent_name: str = Field(min_length=1, max_length=100)
    result: PlayerResult
    """Cómo acabó **para el usuario**, no "1-0": desde su punto de vista no
    hay forma de equivocarse de bando."""
    played_on: dt.date
    username: str | None = None
    """A quién se le atribuye; si se omite, el de `CHESSCOM_USERNAME`."""


async def get_own_game(session: AsyncSession, board: Board) -> Game | None:
    """La partida en la que está publicado el tablero, o `None` si no lo
    está."""
    if board.own_game_id is None:
        return None
    return await session.get(Game, board.own_game_id)


async def get_own_game_with_details(
    session: AsyncSession, board: Board
) -> tuple[Game, OwnGameDetails] | None:
    """La partida publicada del tablero y los datos con los que se publicó,
    para que la pantalla los vuelva a enseñar y se puedan corregir. `None` si
    el tablero no está marcado como partida propia."""
    game = await get_own_game(session, board)
    if game is None:
        return None
    player = await session.get(Player, game.player_id)
    username = player.username if player is not None else game.white_username
    player_color: PlayerColor = (
        "white" if game.white_username.lower() == username.lower() else "black"
    )
    player_result = game.white_result if player_color == "white" else game.black_result
    details = OwnGameDetails(
        player_color=player_color,
        opponent_name=game.black_username if player_color == "white" else game.white_username,
        result=player_result if player_result in ("win", "draw") else "loss",
        played_on=game.played_at.date(),
        username=username,
    )
    return game, details


async def publish_board_as_own_game(
    session: AsyncSession, board: Board, *, details: OwnGameDetails, username: str, pgn: str
) -> Game:
    """Publica el tablero en el historial como partida propia, o actualiza la
    partida ya publicada si se vuelve a marcar con otros datos.

    `pgn` es la salida de `tree.ts::toPgn`: el árbol entero, con sus variantes
    y comentarios. Se guarda tal cual —con cabeceras— porque el visor y la
    exportación leen `games.pgn`, y el análisis recorre solo su línea
    principal, igual que el de cualquier partida.
    """
    player = await get_or_create_player(session, username)
    game = await get_own_game(session, board)
    if game is None:
        game = Game(platform=BOARD_PLATFORM, platform_id=str(board.id))
        session.add(game)

    game.player_id = player.id
    set_pgn_and_opening(game, _build_pgn_with_headers(pgn, details, username=username))
    game.white_username = username if details.player_color == "white" else details.opponent_name
    game.black_username = details.opponent_name if details.player_color == "white" else username
    game.white_rating = 0
    game.black_rating = 0
    # Por la misma tabla que las partidas de un PGN manual (RF-1.5): el
    # resultado del usuario se pasa a notación PGN y de ahí al vocabulario
    # por bando que usan las estadísticas.
    game.white_result, game.black_result = SIDE_RESULTS_BY_PGN_RESULT[
        _PGN_RESULT_BY_COLOR_AND_RESULT[(details.player_color, details.result)]
    ]
    game.time_control = UNKNOWN_TIME_CONTROL
    game.time_class = UNKNOWN_TIME_CLASS
    game.rules = "chess"
    game.rated = False
    game.eco = None
    game.clocks_json = None
    game.played_at = dt.datetime.combine(details.played_on, dt.time.min, tzinfo=dt.UTC)
    game.year = game.played_at.year
    game.month = game.played_at.month

    await session.flush()  # hace falta el id para enlazar el tablero
    board.own_game_id = game.id
    await link_analyses_to_own_game(session, board, analyzed_pgn=pgn)
    return game


async def refresh_own_game_moves(session: AsyncSession, board: Board, pgn: str) -> None:
    """Pone al día las jugadas de la partida publicada con las del tablero.

    Un tablero se sigue editando después de marcarlo, y el historial no puede
    quedarse enseñando una partida que ya no es la que hay en el tablero. Lo
    llama `PUT /boards/{id}` cada vez que el árbol cambia; las cabeceras
    —quién jugó, cómo acabó, qué día— no se tocan, porque eso lo dijo el
    usuario y editar jugadas no lo cambia.

    No hace nada si el tablero no está publicado, que es el caso de casi
    todos.
    """
    published = await get_own_game_with_details(session, board)
    if published is None:
        return
    game, details = published
    username = details.username or game.white_username
    set_pgn_and_opening(game, _build_pgn_with_headers(pgn, details, username=username))
    await link_analyses_to_own_game(session, board, analyzed_pgn=pgn)


async def unpublish_own_game(session: AsyncSession, board: Board) -> None:
    """Retira la marca de partida propia: el tablero deja de contar y su
    partida se va del historial.

    Se borra la fila en vez de dejarla marcada como "no cuenta": el historial
    es lo que el usuario jugó, y una partida que él mismo ha dicho que no es
    suya no tiene por qué seguir ahí ocupando el listado y los filtros.
    """
    game = await get_own_game(session, board)
    board.own_game_id = None
    await link_analyses_to_own_game(session, board, analyzed_pgn=None)
    if game is not None:
        await session.delete(game)


async def link_analyses_to_own_game(
    session: AsyncSession, board: Board, *, analyzed_pgn: str | None
) -> None:
    """Decide cuáles de los análisis del tablero cuentan como análisis de su
    partida publicada.

    Cuenta el que se hizo sobre **estas mismas** jugadas: `analyzed_pgn` es lo
    que hay ahora en el tablero, y un análisis cuyo PGN no coincida es de una
    versión anterior. Es la misma regla que ya avisa en pantalla
    (`tree.ts::matchAnalyzedLine`), aplicada a lo que el dashboard cuenta.

    `analyzed_pgn=None` desenlaza todos: es lo que hace falta al retirar la
    marca y al guardar un tablero cuyo árbol cambió sin que se sepa cómo
    quedó su PGN.
    """
    analyses = (
        (await session.execute(select(Analysis).where(Analysis.board_id == board.id)))
        .scalars()
        .all()
    )
    for analysis in analyses:
        counts = analyzed_pgn is not None and analysis.analyzed_pgn == analyzed_pgn
        analysis.game_id = board.own_game_id if counts else None


#: Resultado en notación PGN según de qué color jugó el usuario y cómo le fue.
_PGN_RESULT_BY_COLOR_AND_RESULT: dict[tuple[PlayerColor, PlayerResult], str] = {
    ("white", "win"): "1-0",
    ("white", "loss"): "0-1",
    ("black", "win"): "0-1",
    ("black", "loss"): "1-0",
    ("white", "draw"): "1/2-1/2",
    ("black", "draw"): "1/2-1/2",
}


def _build_pgn_with_headers(board_pgn: str, details: OwnGameDetails, *, username: str) -> str:
    """El PGN del tablero con las cabeceras de una partida de verdad.

    Se vuelve a leer y a escribir con `chess.pgn` en vez de pegar texto: así
    las variantes, los comentarios y el `[FEN ...]` de un tablero que no
    arranca en la posición estándar se conservan, y el `*` del final queda
    sustituido por el resultado sin buscarlo a mano.
    """
    parsed = chess.pgn.read_game(io.StringIO(board_pgn))
    if parsed is None:
        raise ValueError("el PGN del tablero no se pudo leer")
    parsed.headers["Event"] = "Partida propia"
    parsed.headers["Site"] = "LUCIA"
    parsed.headers["Date"] = details.played_on.strftime("%Y.%m.%d")
    parsed.headers["White"] = username if details.player_color == "white" else details.opponent_name
    parsed.headers["Black"] = details.opponent_name if details.player_color == "white" else username
    parsed.headers["Result"] = _PGN_RESULT_BY_COLOR_AND_RESULT[
        (details.player_color, details.result)
    ]
    return str(parsed)

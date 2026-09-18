"""Importación de PGN manual (RF-1.5): partidas jugadas fuera de chess.com
—sobre el tablero, en lichess, de un archivo de torneo— al mismo historial.

Entra un archivo `.pgn` con una o muchas partidas y sale lo mismo que deja el
sincronizador de chess.com: filas de `games` colgando de un `Player`, con su
apertura deducida y sus relojes extraídos. A partir de ahí el visor, el
análisis y las estadísticas no distinguen de dónde vino la partida.

Dos cosas que el PGN manual no trae y chess.com sí:

- **Quién es el usuario.** En un PGN de torneo el jugador aparece como
  "Durán, Jesús", no con su usuario de chess.com, así que las estadísticas
  —que casan por nombre— no lo reconocerían. Por eso `player_name_in_pgn` dice cómo
  aparece el usuario en ese archivo y ese lado se guarda con su `username` de
  LUCIA. El nombre original no se pierde: el PGN se guarda entero en la fila.
- **Rating, control de tiempo y si era de competición.** Casi ningún PGN de
  otra fuente los trae, y las columnas son obligatorias porque en chess.com
  siempre vienen. Se rellenan con huecos —rating 0, ritmo "unknown"— en vez
  de inventarlos: ni el PGN dice a qué ritmo se jugó ni hay forma de
  deducirlo sin equivocarse (un "40/7200:1800" de torneo no es ninguna de
  las categorías de chess.com).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io

import chess.pgn
from lucia_chesscom import parse_move_clocks
from lucia_core.openings import opening_of_pgn
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Game, Player

#: Resultado del PGN traducido al vocabulario por bando que usa `games`
#: (ver `lucia_api.services.games`). Una partida sin terminar ("*") no está
#: aquí a propósito: no se importa.
_SIDE_RESULTS_BY_PGN_RESULT = {
    "1-0": ("win", "loss"),
    "0-1": ("loss", "win"),
    "1/2-1/2": ("draw", "draw"),
}


class PgnImportSummary(BaseModel):
    """Qué pasó con cada partida del archivo."""

    games_imported: int
    """Partidas nuevas guardadas."""
    games_already_present: int
    """Partidas que ya estaban (mismo contenido): se reescriben, no se duplican."""
    skipped_game_reasons: list[str]
    """Una línea por partida que no se pudo importar, con el motivo."""
    games_matched_to_player: int
    """De las guardadas, en cuántas se reconoció al usuario en uno de los dos
    bandos. Es lo que decide si la partida cuenta en el dashboard y en los
    filtros por color, resultado y rival, que casan por nombre: sin esto, un
    `player_name_in_pgn` mal escrito importaría las partidas en silencio y el usuario
    lo descubriría días después, al no verlas en ningún marcador."""


async def import_pgn(
    session: AsyncSession,
    pgn_text: str,
    *,
    username: str,
    player_name_in_pgn: str | None = None,
) -> PgnImportSummary:
    """Guarda las partidas de `pgn_text` en el historial de `username`.

    `player_name_in_pgn` es cómo aparece el usuario dentro de ese PGN; si coincide
    con uno de los dos bandos, ese bando se guarda como `username` para que
    las partidas cuenten en el dashboard y en los filtros por color, resultado
    y rival (RF-3, RF-5.3).
    """
    player = await _get_or_create_player(session, username)

    imported = 0
    already_present = 0
    matched_to_player = 0
    skip_reasons: list[str] = []
    pgn_stream = io.StringIO(pgn_text)
    position_in_file = 0

    while (parsed_game := chess.pgn.read_game(pgn_stream)) is not None:
        position_in_file += 1
        problem = _find_import_problem(parsed_game)
        if problem:
            white = parsed_game.headers.get("White", "?")
            black = parsed_game.headers.get("Black", "?")
            skip_reasons.append(f"Partida {position_in_file} ({white} vs {black}): {problem}")
            continue
        game, was_new = await _upsert_game(
            session,
            player.id,
            parsed_game,
            username=username,
            player_name_in_pgn=player_name_in_pgn,
        )
        if was_new:
            imported += 1
        else:
            already_present += 1
        if username.lower() in (game.white_username.lower(), game.black_username.lower()):
            matched_to_player += 1

    await session.commit()
    return PgnImportSummary(
        games_imported=imported,
        games_already_present=already_present,
        skipped_game_reasons=skip_reasons,
        games_matched_to_player=matched_to_player,
    )


def _find_import_problem(parsed_game: chess.pgn.Game) -> str | None:
    """Por qué esta partida no se puede guardar, o `None` si se puede."""
    if not parsed_game.variations:
        return "no trae jugadas."
    if parsed_game.headers.get("Result") not in _SIDE_RESULTS_BY_PGN_RESULT:
        return f"resultado «{parsed_game.headers.get('Result', '?')}», sin terminar o ilegible."
    return None


async def _get_or_create_player(session: AsyncSession, username: str) -> Player:
    """El jugador al que se atribuyen las partidas importadas.

    Se busca por nombre en cualquier plataforma para caer en la **misma** fila
    que creó la sincronización con chess.com: si fueran dos jugadores, el
    historial quedaría partido en dos. Solo cuando no existe ninguno se crea
    uno de plataforma "manual", que es el caso de quien nunca sincronizó.
    """
    result = await session.execute(select(Player).where(Player.username == username))
    player = result.scalars().first()
    if player is None:
        player = Player(platform="manual", username=username)
        session.add(player)
        await session.flush()  # asigna player.id sin cerrar la transacción
    return player


async def _upsert_game(
    session: AsyncSession,
    player_id: int,
    parsed_game: chess.pgn.Game,
    *,
    username: str,
    player_name_in_pgn: str | None,
) -> tuple[Game, bool]:
    """Guarda una partida; devuelve la fila y si era nueva."""
    headers = parsed_game.headers
    pgn_text = str(parsed_game)
    # El identificador es el contenido del PGN: un archivo manual no trae
    # identificador de partida, y así reimportar el mismo archivo reescribe
    # las mismas filas en vez de duplicarlas.
    platform_id = hashlib.sha256(pgn_text.encode()).hexdigest()

    result = await session.execute(
        select(Game).where(Game.platform == "manual", Game.platform_id == platform_id)
    )
    game = result.scalar_one_or_none()
    was_new = game is None
    if game is None:
        game = Game(player_id=player_id, platform="manual", platform_id=platform_id)
        session.add(game)

    white_result, black_result = _SIDE_RESULTS_BY_PGN_RESULT[headers["Result"]]
    game.pgn = pgn_text
    game.white_username = _resolve_side_username(
        headers.get("White", "?"), player_name_in_pgn, username
    )
    game.black_username = _resolve_side_username(
        headers.get("Black", "?"), player_name_in_pgn, username
    )
    game.white_rating = _parse_rating(headers.get("WhiteElo"))
    game.black_rating = _parse_rating(headers.get("BlackElo"))
    game.white_result = white_result
    game.black_result = black_result
    game.time_control = headers.get("TimeControl") or "-"
    game.time_class = "unknown"
    game.rules = "chess"
    game.rated = False
    game.eco = headers.get("ECO")
    opening = opening_of_pgn(pgn_text)
    game.opening_eco = opening.eco if opening else None
    game.opening_name = opening.name if opening else None
    game.clocks_json = parse_move_clocks(pgn_text)
    game.played_at = _parse_played_at(headers)
    game.year = game.played_at.year
    game.month = game.played_at.month
    return game, was_new


def _resolve_side_username(
    side_name_in_pgn: str, player_name_in_pgn: str | None, username: str
) -> str:
    """El nombre con el que se guarda un bando: el del PGN, salvo que sea el
    del usuario, que se guarda con su `username` de LUCIA."""
    if (
        player_name_in_pgn
        and side_name_in_pgn.strip().lower() == player_name_in_pgn.strip().lower()
    ):
        return username
    return side_name_in_pgn


def _parse_rating(elo_header: str | None) -> int:
    """El rating de un bando, o 0 si el PGN no lo trae (el hueco de la columna)."""
    return int(elo_header) if elo_header and elo_header.isdigit() else 0


def _parse_played_at(headers: chess.pgn.Headers) -> dt.datetime:
    """Cuándo se jugó, de `UTCDate`/`UTCTime` o, si no están, de `Date`.

    Un PGN puede no traer fecha ("????.??.??") o traerla sin hora. Sin fecha
    se usa la de la importación, para que la partida no acabe ordenada en un
    sitio arbitrario del historial; sin hora, la medianoche del día.
    """
    date_header = headers.get("UTCDate") or headers.get("Date") or ""
    try:
        day = dt.datetime.strptime(date_header, "%Y.%m.%d").date()
    except ValueError:
        return dt.datetime.now(dt.UTC)
    try:
        time_of_day = dt.datetime.strptime(headers.get("UTCTime", ""), "%H:%M:%S").time()
    except ValueError:
        time_of_day = dt.time.min
    return dt.datetime.combine(day, time_of_day, tzinfo=dt.UTC)

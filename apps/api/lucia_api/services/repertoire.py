"""Comparación del repertorio propio con la teoría de maestros (RF-3.6).

La pregunta que responde: **dónde me salgo de la línea principal y con qué
resultado**. Se recorre cada partida desde el principio y, en cada posición en
la que le toca mover al jugador, se mira qué juegan los maestros en esa misma
posición (base del Opening Explorer de Lichess). La primera jugada propia que
no está en ese repertorio es el punto de salida de la teoría.

**Se para al salir.** Una vez fuera del libro, lo que venga después ya no dice
nada del repertorio: si transpones de vuelta a una posición conocida por
casualidad, no significa que la estuvieras siguiendo. Es la misma regla que
`lucia_core.openings` aplica al nombrar la apertura.

**La red y el cálculo van por separado** (ver ADR-0010):

- `refresh_repertoire` es lo único que sale a internet. Pregunta por las
  posiciones que hacen falta y las guarda, con un tope por llamada para no
  dejar una petición HTTP colgada varios minutos.
- `compare_repertoire` no sale a internet nunca: lee lo que haya en la caché.
  Sin conexión sigue respondiendo con lo que ya se preguntó, y dice cuánto le
  falta por saber.

Quién lo usa: el router `repertoire` (la pantalla de estadísticas) y, desde
RF-4.2, `services/drills.py`, que convierte cada salida en una línea para
repetir jugando. Por eso una `Departure` lleva además el camino que se recorrió
hasta ella y la jugada de maestros en UCI, que la comparación no mira.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from dataclasses import dataclass, field

import chess
import chess.pgn
from lucia_lichess import ExplorerPosition, LichessExplorerClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import ExplorerPositionCache, Game
from lucia_api.services.games import is_white

#: Hasta qué jugada se compara. Más allá de la 8 de cada bando, "salirse de la
#: teoría" deja de ser una decisión de repertorio y pasa a ser jugar al ajedrez.
MAX_REPERTOIRE_PLIES = 16

#: Cuántas partidas de maestros tiene que tener una jugada para contar como
#: repertorio. Una sola partida en la base no es teoría, es una anécdota.
MIN_MASTER_GAMES = 5

#: Tope de consultas por llamada a `refresh_repertoire`. Al ritmo al que se
#: espaciáan (una por segundo), es aproximadamente el minuto que puede tardar
#: una petición sin resultar rara.
DEFAULT_REFRESH_BUDGET = 25


@dataclass(frozen=True)
class PlayerMove:
    """Una decisión del jugador en la apertura de una de sus partidas."""

    game_id: int
    ply: int
    epd: str
    """La posición **antes** de la jugada, que es de la que se pregunta teoría."""
    fen: str
    san: str
    uci: str
    color: str
    outcome: str
    """Cómo acabó esa partida para el jugador: "win", "draw" o "loss"."""
    preceding_moves_uci: tuple[str, ...] = ()
    """Las jugadas de los dos bandos anteriores a esta. Solo la usa el drill
    (RF-4.2), para poder repetir la línea entera; la comparación de repertorio
    no la mira."""


@dataclass
class Departure:
    """Un punto de salida de la teoría, agrupando todas las partidas que se
    salen por ahí con la misma jugada."""

    ply: int
    san: str
    """La jugada propia que ya no es teoría."""
    color: str
    master_moves: list[str] = field(default_factory=list)
    """Lo que juegan los maestros en esa posición, de más a menos frecuente."""
    master_moves_uci: list[str] = field(default_factory=list)
    """Las mismas, en UCI. Las dos notaciones porque cada consumidor quiere la
    suya: la pantalla de repertorio enseña el SAN, y el drill de RF-4.2
    necesita el UCI para componer la línea que se repite."""
    preceding_moves_uci: list[str] = field(default_factory=list)
    """Las jugadas —de los dos bandos— que llevaron hasta aquí, de la primera
    partida del grupo que se salió por este punto. Es el camino hasta la
    decisión, y con él el drill de RF-4.2 puede reproducir la línea entera en
    vez de plantar al usuario en una posición suelta.

    De una partida cualquiera del grupo y no de todas: las jugadas propias son
    las mismas por definición —se agrupa por color, momento y jugada—, y las
    del rival hasta ahí son de libro. Si no fueran las mismas, la posición
    sería otra y el grupo también."""
    opening: str | None = None
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def score_percent(self) -> float:
        if self.games == 0:
            return 0.0
        return (self.wins + self.draws * 0.5) / self.games * 100


@dataclass
class RepertoireComparison:
    """Lo que se sabe del repertorio de un jugador, y lo que falta por saber."""

    departures: list[Departure] = field(default_factory=list)
    games_compared: int = 0
    """Partidas en las que ya se pudo localizar la salida de la teoría."""
    positions_known: int = 0
    positions_missing: int = 0
    """Posiciones que aún no se le han preguntado a Lichess. Mientras no sea
    cero, la comparación está incompleta y la pantalla lo dice."""


async def _player_moves(session: AsyncSession, username: str) -> list[list[PlayerMove]]:
    """Las decisiones de apertura del jugador, partida a partida y en orden.

    Cada lista es una partida; recorrerla es lo que permite parar en cuanto se
    sale de la teoría, sin mirar el resto.

    Las partidas que no empiezan en la posición estándar quedan fuera: sin
    teoría de la que salirse, no hay repertorio que comparar.
    """
    rows = (
        await session.execute(
            select(
                Game.id, Game.pgn, is_white(username).label("player_is_white"), Game.opening_name
            )
        )
    ).all()

    games: list[list[PlayerMove]] = []
    for game_id, pgn, player_is_white, opening_name in rows:
        moves = list(_opening_moves(game_id, pgn, bool(player_is_white), opening_name))
        if moves:
            games.append(moves)
    return games


def _opening_moves(
    game_id: int, pgn: str, player_is_white: bool, opening_name: str | None
) -> Iterator[PlayerMove]:
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return
    board = game.board()
    if board.fen() != chess.STARTING_FEN:
        return
    outcome = _outcome_from_headers(game.headers.get("Result", "*"), player_is_white)

    moves_so_far: list[str] = []
    for ply, move in enumerate(game.mainline_moves()):
        if ply >= MAX_REPERTOIRE_PLIES:
            return
        if (ply % 2 == 0) == player_is_white:
            yield PlayerMove(
                game_id=game_id,
                ply=ply,
                epd=board.epd(),
                fen=board.fen(),
                san=board.san(move),
                uci=move.uci(),
                color="white" if player_is_white else "black",
                outcome=outcome,
                preceding_moves_uci=tuple(moves_so_far),
            )
        moves_so_far.append(move.uci())
        board.push(move)


def _outcome_from_headers(result: str, player_is_white: bool) -> str:
    """El resultado desde el lado del jugador, leído del PGN.

    Se saca del PGN y no de las columnas `white_result`/`black_result` porque
    aquí ya se está recorriendo la partida, y son el mismo dato.
    """
    if result == "1/2-1/2":
        return "draw"
    if result == "1-0":
        return "win" if player_is_white else "loss"
    if result == "0-1":
        return "loss" if player_is_white else "win"
    return "draw"  # partida sin resultado: no cuenta ni a favor ni en contra


async def _cached_positions(session: AsyncSession, epds: set[str]) -> dict[str, ExplorerPosition]:
    """Lo que ya se sabe de esas posiciones, sin preguntar a nadie."""
    if not epds:
        return {}
    rows = (
        await session.execute(
            select(ExplorerPositionCache.epd, ExplorerPositionCache.masters_json).where(
                ExplorerPositionCache.epd.in_(epds)
            )
        )
    ).all()
    return {epd: ExplorerPosition.model_validate(masters) for epd, masters in rows}


def _is_in_the_book(position: ExplorerPosition, uci: str) -> bool:
    """Si esa jugada es repertorio en esa posición.

    No basta con que aparezca: tiene que aparecer lo bastante
    (`MIN_MASTER_GAMES`). Una jugada con dos partidas en la base de maestros no
    es la línea principal de la que hablamos.
    """
    return any(move.uci == uci and move.games >= MIN_MASTER_GAMES for move in position.moves)


def _move_that_leaves_the_book(
    game_moves: list[PlayerMove], known: dict[str, ExplorerPosition]
) -> PlayerMove | None:
    """La jugada con la que esa partida deja de seguir la teoría, o `None` si
    no deja de seguirla en el tramo que se compara.

    Es el recorrido que comparten las dos preguntas de este módulo. Si el EPD
    de la jugada devuelta no está en `known`, la partida no se salió: es que
    todavía no se sabe la teoría de ahí y hay que preguntarla.
    """
    for move in game_moves:
        position = known.get(move.epd)
        if position is None:
            return move  # sin teoría de aquí no se puede seguir esta partida
        if position.games < MIN_MASTER_GAMES:
            return None  # la posición ya no es de libro: no hay de qué salirse
        if not _is_in_the_book(position, move.uci):
            return move
    return None


async def _games_and_book(
    session: AsyncSession, username: str
) -> tuple[list[list[PlayerMove]], dict[str, ExplorerPosition]]:
    """Las aperturas del jugador y la teoría que ya se sabe de ellas."""
    games = await _player_moves(session, username)
    known = await _cached_positions(
        session, {move.epd for game_moves in games for move in game_moves}
    )
    return games, known


async def compare_repertoire(session: AsyncSession, username: str) -> RepertoireComparison:
    """Dónde se sale el jugador de la teoría, con lo que ya se sabe (RF-3.6).

    No sale a internet: si falta teoría de alguna posición, esa partida se
    queda sin comparar y se cuenta en `positions_missing`, para que la pantalla
    pueda decir que la foto está incompleta en vez de dar por buena una
    comparación a medias.
    """
    games, known = await _games_and_book(session, username)

    departures: dict[tuple[str, int, str], Departure] = {}
    missing: set[str] = set()
    games_compared = 0

    for game_moves in games:
        move = _move_that_leaves_the_book(game_moves, known)
        if move is None:
            continue
        position = known.get(move.epd)
        if position is None:
            missing.add(move.epd)
            continue

        # Las que se enseñan de esa posición, elegidas una vez y escritas
        # luego en las dos notaciones (ver `Departure`): si se eligieran dos
        # veces, la pantalla y el drill podrían no coincidir.
        master_moves = [
            master_move for master_move in position.moves if master_move.games >= MIN_MASTER_GAMES
        ][:3]
        departure = departures.setdefault(
            (move.color, move.ply, move.san),
            Departure(
                ply=move.ply,
                san=move.san,
                color=move.color,
                master_moves=[master_move.san for master_move in master_moves],
                master_moves_uci=[master_move.uci for master_move in master_moves],
                preceding_moves_uci=list(move.preceding_moves_uci),
            ),
        )
        departure.games += 1
        if move.outcome == "win":
            departure.wins += 1
        elif move.outcome == "draw":
            departure.draws += 1
        else:
            departure.losses += 1
        games_compared += 1

    return RepertoireComparison(
        # Primero lo que más se repite: es lo que más veces cuesta puntos.
        departures=sorted(departures.values(), key=lambda item: item.games, reverse=True),
        games_compared=games_compared,
        positions_known=len(known),
        positions_missing=len(missing),
    )


async def refresh_repertoire(
    session: AsyncSession,
    client: LichessExplorerClient,
    username: str,
    budget: int = DEFAULT_REFRESH_BUDGET,
) -> tuple[int, int]:
    """Pregunta a Lichess por las posiciones que faltan y las guarda.

    Devuelve `(cuántas se preguntaron, cuántas siguen faltando)`. El tope
    existe porque la primera vez pueden faltar cientos y se pregunta de una en
    una, espaciadas: sin él, la petición HTTP se quedaría colgada varios
    minutos. Volver a llamar sigue por donde se quedó.

    Si el explorador falla a mitad —sin red, o limitando—, se guarda lo
    conseguido hasta ahí y se propaga el error: media caché es mejor que
    ninguna, y quien llama tiene que poder decirlo.
    """
    fetched = 0
    try:
        while fetched < budget:
            pending = await _missing_positions(session, username, budget - fetched)
            if not pending:
                break
            for epd, fen in pending:
                position = await client.masters(fen)
                session.add(
                    ExplorerPositionCache(epd=epd, masters_json=position.model_dump(mode="json"))
                )
                await session.flush()
                fetched += 1
    finally:
        await session.commit()

    remaining = (await compare_repertoire(session, username)).positions_missing
    return fetched, remaining


async def _missing_positions(
    session: AsyncSession, username: str, limit: int
) -> list[tuple[str, str]]:
    """Las posiciones que hacen falta ahora mismo, como `(epd, fen)`.

    Se recalculan en cada ronda a propósito: saber la teoría de una posición
    destapa la siguiente de esa misma partida, así que la lista crece según se
    va rellenando y no se puede calcular entera de antemano.
    """
    games, known = await _games_and_book(session, username)

    missing: dict[str, str] = {}
    for game_moves in games:
        move = _move_that_leaves_the_book(game_moves, known)
        if move is not None and move.epd not in known:
            missing.setdefault(move.epd, move.fen)
            if len(missing) >= limit:
                break
    return list(missing.items())

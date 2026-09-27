"""Jugar contra el motor con la fuerza calibrada (RF-4.3), desde el principio o
retomando una partida propia desde donde se torció (RF-4.4).

Aquí se juntan las tres piezas: las reglas puras de `lucia_core.sparring` —qué
posición hay ahora y si la partida acabó—, el motor de `lucia_core.engine` —que
desde RF-4.3 sabe **jugar** además de analizar— y la fila de `sparring_games`,
que guarda la posición de partida y las jugadas y nada más.

**Retomar no es otra forma de jugar**, es la misma empezada en otro sitio: la
misma tabla, el mismo ciclo y la misma pantalla, con `starting_fen` en otra
posición y `origin_game_id`/`origin_ply` diciendo de dónde salió. Por eso vive
en este módulo y no en uno propio; quién elige *qué* posición merece retomarse
es `services/replays.py`, que solo lista. Razonado en
[ADR-0020](../../../../docs/adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md).

**Quién calibra la fuerza es este módulo**, y no el núcleo: depende de qué
motor haya instalado y de con qué red, que es información de la instalación
(`.env`, `Settings`) y no una regla de ajedrez. Las dos maneras de tener un
rival flojo son distintas de raíz:

- **Stockfish** busca igual de bien y se le pide que juegue peor, con
  `UCI_LimitStrength` y un `UCI_Elo` entre 1320 y 3190. Es un Elo elegible, y
  el rival es un motor de verdad conteniéndose.
- **Lc0 con una red Maia** no se contiene: la red está entrenada para predecir
  la jugada que haría un humano de ~1500, así que sus errores son los que
  comete la gente, no los que comete un motor mutilado. Su fuerza no se pide
  por UCI —es la de la red— y se juega a **un solo nodo**, que es como Maia se
  usa: con más nodos la búsqueda empieza a corregir a la red y se pierde justo
  lo que la hace humana.

De ahí que `engine_elo` solo tenga sentido con Stockfish, y que la pantalla
tenga que decirlo en vez de enseñar un deslizador muerto.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import chess
from lucia_core.engine import EngineBridge, EngineConfig
from lucia_core.sparring import (
    GameEnding,
    board_after_moves,
    board_at_ply,
    ending_of,
    resignation_ending,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lucia_api.db.models import Game, SparringGame
from lucia_api.settings import settings

SPARRING_ENGINE_NAMES = ("stockfish", "lc0")

#: Topes de `UCI_Elo` en Stockfish 17. No son un gusto: por debajo de 1320 el
#: motor no acepta el valor, y por encima de 3190 ya no se está limitando
#: nada. Se comprueban al crear la partida para que un valor imposible dé un
#: 422 y no un motor que aborta a mitad.
STOCKFISH_ELO_RANGE = (1320, 3190)

#: Cuánto piensa Stockfish en cada jugada. Un segundo es de sobra para que un
#: Elo limitado juegue a su nivel —lo que lo frena es `UCI_LimitStrength`, no
#: el tiempo— y es lo que quien juega está dispuesto a esperar entre jugada y
#: jugada.
STOCKFISH_MOVE_SECONDS = 1

#: Nodos por jugada de Lc0 con Maia: uno. Ver la explicación de arriba.
MAIA_NODES = 1


def engine_config(engine_name: str, engine_elo: int | None) -> EngineConfig:
    """La configuración con la que se abre el motor para que juegue.

    No reutiliza `services/engines.py::get_effective_config` a propósito: eso
    es lo que el usuario ajustó **para analizar** (profundidad, MultiPV), y
    aquí no se analiza nada. Lo que importa es la fuerza y que conteste rápido.
    """
    if engine_name == "stockfish":
        if engine_elo is None:
            raise ValueError("una partida contra Stockfish necesita un Elo")
        return EngineConfig(
            name="stockfish",
            path=settings.stockfish_path,
            multipv=1,
            limit_kind="time",
            limit_value=STOCKFISH_MOVE_SECONDS,
            extra_options={"UCI_LimitStrength": True, "UCI_Elo": engine_elo},
        )

    uci_options: dict[str, str | int | bool] = {"WeightsFile": str(settings.maia_weights)}
    if settings.lc0_backend:
        uci_options["Backend"] = settings.lc0_backend
    return EngineConfig(
        name="lc0",
        path=settings.lc0_path,
        multipv=1,
        limit_kind="nodes",
        limit_value=MAIA_NODES,
        extra_options=uci_options,
    )


def missing_requirement(engine_name: str) -> str | None:
    """Qué le falta a la instalación para poder jugar contra este motor, o
    `None` si no le falta nada.

    Se comprueba antes de abrir nada porque el fallo de un motor que no está
    llega como un error de proceso —una traza del binario, o el silencio de
    Lc0 sin red— y quien acaba de clonar el repo no tiene por qué deducir de
    ahí que le falta `make engines`. La pantalla de motores ya hace lo mismo
    con las rutas de análisis (RF-5.4).
    """
    config = engine_config(engine_name, STOCKFISH_ELO_RANGE[0])
    if not config.path.exists():
        return f"{engine_name} no está compilado en {config.path}. Ejecuta 'make engines'."
    if engine_name == "lc0" and not settings.maia_weights.exists():
        return (
            f"falta la red Maia en {settings.maia_weights}. "
            "Ejecuta 'make engines', que la descarga."
        )
    return None


@dataclass(frozen=True)
class SparringOrigin:
    """Una posición de una partida propia, para retomarla desde ahí (RF-4.4)."""

    game_id: int
    ply: int
    """Jugadas ya hechas: 0 es el principio, y `ply` es la posición **anterior**
    a la jugada número `ply`. Así, retomar justo antes de un error es pedir el
    ply de ese error, que es como lo numera `AnalyzedMove`."""
    fen: str


async def get_sparring_origin(session: AsyncSession, game_id: int, ply: int) -> SparringOrigin:
    """La posición de una partida propia en esa jugada (RF-4.4).

    La posición se deriva del PGN que ya está guardado en vez de pedírsela a
    la pantalla: el servidor es quien va a jugar desde ahí, y aceptar un FEN
    cualquiera por HTTP sería otra cosa —empezar desde una posición inventada,
    que es RF-11.1 y está fuera del alcance de v1.0—.

    Lanza `ValueError` si la partida no existe o no llega a esa jugada.
    """
    game = await session.get(Game, game_id)
    if game is None:
        raise ValueError(f"no existe la partida {game_id}")
    return SparringOrigin(game_id=game_id, ply=ply, fen=board_at_ply(game.pgn, ply).fen())


async def create_game(
    session: AsyncSession,
    *,
    player_color: str,
    engine_name: str,
    engine_elo: int | None,
    origin: SparringOrigin | None = None,
) -> SparringGame:
    """Abre una partida y, si le toca mover al motor, le pide ya su jugada.

    Que el motor abra aquí y no en la primera petición de la pantalla es lo
    que hace que la partida llegue lista para mover: si no, quien juega con el
    otro bando vería un tablero esperando a nadie.

    Con `origin` la partida no empieza en la posición inicial sino en la de una
    partida propia (RF-4.4): se guarda esa posición y de dónde salió, para
    poder decirlo en pantalla y volver a ver la partida en el visor.
    """
    game = SparringGame(
        player_color=player_color,
        engine=engine_name,
        engine_elo=engine_elo if engine_name == "stockfish" else None,
        starting_fen=origin.fen if origin else chess.STARTING_FEN,
        moves_uci_json=[],
        origin_game_id=origin.game_id if origin else None,
        origin_ply=origin.ply if origin else None,
    )
    session.add(game)
    await session.flush()

    # Quién abre no es "las blancas": es quien tenga el turno en la posición de
    # partida, que retomando una partida a mitad puede ser cualquiera.
    if current_board(game).turn != _color_of(player_color):
        await _play_engine_move(game)
    await session.commit()
    return game


async def play_player_move(session: AsyncSession, game: SparringGame, uci: str) -> SparringGame:
    """Juega la jugada de la persona y, si la partida sigue, contesta el motor.

    Las dos van en la misma petición porque son un solo turno para quien
    juega: partirlas obligaría a la pantalla a encadenar dos llamadas y a
    lidiar con el estado intermedio "he movido pero el motor no".

    Lanza `ValueError` si la partida ya terminó, si no es el turno de la
    persona o si la jugada no es legal.
    """
    board = current_board(game)
    if game.result is not None:
        raise ValueError("esa partida ya terminó")
    if board.turn != _color_of(game.player_color):
        raise ValueError("no es tu turno")

    move = _parse_legal_move(board, uci)
    _append_move(game, board, move)
    if game.result is None:
        await _play_engine_move(game)
    await session.commit()
    return game


async def resign(session: AsyncSession, game: SparringGame) -> SparringGame:
    """Abandona: gana el motor. Es la única forma de cerrar una partida que no
    sale del tablero, y por eso no vive en `lucia_core.sparring.ending_of`."""
    if game.result is not None:
        raise ValueError("esa partida ya terminó")
    _finish_game(game, resignation_ending(_color_of(game.player_color)))
    await session.commit()
    return game


async def list_games(session: AsyncSession, limit: int) -> list[SparringGame]:
    """Las partidas de sparring, la más reciente primero. Lo que se está
    jugando ahora encabeza la lista porque `updated_at` es la última jugada."""
    rows = await session.execute(
        select(SparringGame).order_by(SparringGame.updated_at.desc()).limit(limit)
    )
    return list(rows.scalars().all())


def current_board(game: SparringGame) -> chess.Board:
    """La posición que hay ahora, rehecha desde las jugadas guardadas."""
    return board_after_moves(game.starting_fen, game.moves_uci_json)


async def _play_engine_move(game: SparringGame) -> None:
    """Abre el motor, le pide una jugada y la apunta.

    Se abre y se cierra en cada jugada, como ya hace `POST /analysis/position`:
    un proceso vivo por partida habría que guardarlo en algún sitio, cerrarlo
    cuando la pantalla se abandona y compartirlo entre peticiones. Arrancar
    Stockfish cuesta milisegundos y Maia pesa un mega, así que no se nota al
    lado del segundo que tarda en pensar.
    """
    board = current_board(game)
    async with EngineBridge(engine_config(game.engine, game.engine_elo)) as engine:
        move = await engine.play(board)
    _append_move(game, board, move)


def _append_move(game: SparringGame, board: chess.Board, move: chess.Move) -> None:
    """Apunta la jugada y, si con ella se acabó la partida, cierra la fila.

    `moves_uci_json` se reasigna entera en vez de crecer con `append`: es una
    columna JSON, y SQLAlchemy solo detecta que cambió si se le asigna un
    valor nuevo.
    """
    board.push(move)
    game.moves_uci_json = [*game.moves_uci_json, move.uci()]
    game.updated_at = dt.datetime.now(dt.UTC)
    ending = ending_of(board)
    if ending is not None:
        _finish_game(game, ending)


def _finish_game(game: SparringGame, ending: GameEnding) -> None:
    game.result = ending.result
    game.termination = ending.termination
    game.updated_at = dt.datetime.now(dt.UTC)


def _parse_legal_move(board: chess.Board, uci: str) -> chess.Move:
    try:
        move = chess.Move.from_uci(uci)
    except ValueError as error:
        raise ValueError(f"{uci!r} no es una jugada en notación UCI") from error
    if not board.is_legal(move):
        raise ValueError(f"{uci} no es legal en esta posición")
    return move


def _color_of(color_name: str) -> chess.Color:
    return chess.WHITE if color_name == "white" else chess.BLACK

"""Modelo de datos de LUCIA (ver docs/03-arquitectura.md § Modelo de datos).

RF-1 (importación desde chess.com y de un PGN manual): `Player`, `Game`,
`SyncState`.
RF-2 (análisis con motores): `Analysis`, `AnalyzedMove`, `PositionCache`.
RF-5.4 (configuración editable de los motores): `EngineSettings`.
RF-6 (tablero de análisis): `Board` y `BoardVersion`, el historial lineal de
deshacer y rehacer de RF-6.8.
RF-3.6 (comparación de repertorio): `ExplorerPositionCache`, la caché de lo
que se le preguntó al Opening Explorer de Lichess.
RF-4.1 (entrenamiento desde los errores propios): `Puzzle`, con su estado de
repetición espaciada.
RF-4.3 (sparring contra el motor con fuerza calibrada): `SparringGame`.

Las columnas que no se explican solas llevan su porqué al lado; el mapa
completo, con las relaciones y las reglas entre tablas, está en
docs/03-arquitectura.md.
"""

from __future__ import annotations

import datetime as dt
import re

import chess
from sqlalchemy import JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Player(Base):
    """Un jugador importado de una plataforma externa (por ahora, chess.com)."""

    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("platform", "username", name="uq_player_platform_username"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(default="chesscom")
    username: Mapped[str]
    country: Mapped[str | None] = mapped_column(default=None)
    """País del perfil (RF-1.1), tal como lo reporta GET /player/{u}: una URL
    tipo https://api.chess.com/pub/country/MX, no un nombre legible."""
    joined_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    """Fecha de alta del perfil (RF-1.1), de GET /player/{u}."""
    ratings_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    """JSON crudo de GET /player/{u}/stats (RF-1.6): ratings por control de tiempo."""
    fetched_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )

    games: Mapped[list[Game]] = relationship(back_populates="player", cascade="all, delete-orphan")
    sync_state: Mapped[SyncState | None] = relationship(
        back_populates="player", cascade="all, delete-orphan", uselist=False
    )


class Game(Base):
    """Una partida importada, tal como la reportó chess.com (RF-1.2)."""

    __tablename__ = "games"
    __table_args__ = (
        UniqueConstraint("platform", "platform_id", name="uq_game_platform_platform_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    platform: Mapped[str] = mapped_column(default="chesscom")
    platform_id: Mapped[str]
    """`uuid` de chess.com: identifica la partida de forma estable entre sincronizaciones."""

    pgn: Mapped[str]
    white_username: Mapped[str]
    white_rating: Mapped[int]
    white_result: Mapped[str]
    """Resultado tal como lo reporta chess.com: "win" | "checkmated" | "resigned" | ..."""
    black_username: Mapped[str]
    black_rating: Mapped[int]
    black_result: Mapped[str]

    time_control: Mapped[str]
    time_class: Mapped[str]
    rules: Mapped[str]
    rated: Mapped[bool]
    eco: Mapped[str | None] = mapped_column(default=None)
    """Apertura tal como la reporta chess.com: una URL, y no en todas las
    partidas. Se conserva como dato de origen; para agrupar y enseñar se usan
    las dos columnas de abajo."""
    opening_eco: Mapped[str | None] = mapped_column(default=None)
    opening_name: Mapped[str | None] = mapped_column(default=None)
    """Apertura deducida de las jugadas con la tabla ECO propia
    (`lucia_core.openings`, RF-3.2): sale en toda partida que empiece en la
    posición estándar, trae el código ECO —que chess.com no da— y reconoce
    transposiciones. `None` en las que empiezan desde otra posición (odds
    chess, Chess960), donde no hay apertura que nombrar."""
    clocks_json: Mapped[list | None] = mapped_column(JSON, default=None)
    """Reloj restante en segundos tras cada jugada (ver lucia_chesscom.parse_move_clocks)."""

    played_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    """`end_time` de chess.com: cuándo terminó la partida."""
    year: Mapped[int]
    month: Mapped[int]
    """Mes del archivo de chess.com al que pertenece; evita reparsear `played_at` al sincronizar."""

    player: Mapped[Player] = relationship(back_populates="games")
    analyses: Mapped[list[Analysis]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )

    @property
    def starts_from_custom_position(self) -> bool:
        """Si la partida no arranca en la posición estándar.

        chess.com marca esas partidas con `[SetUp "1"]` + `[FEN ...]` en el
        PGN: odds chess, Chess960 y "partidas desde posición". Se mira con una
        expresión regular sobre la cabecera y no con `chess.pgn.read_game`
        porque el listado devuelve decenas de partidas por petición y aquí
        solo hace falta el FEN inicial, no el árbol de jugadas.

        La interfaz lo usa para avisar de que el tablero que se ve es el de la
        partida y no un fallo (criterio C-6 de docs/07-coherencia-ui.md).
        """
        starting_fen = re.search(r'\[FEN "([^"]+)"\]', self.pgn)
        return starting_fen is not None and starting_fen.group(1) != chess.STARTING_FEN


class SyncState(Base):
    """Progreso de sincronización incremental por jugador (RF-1.3)."""

    __tablename__ = "sync_state"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    last_synced_year: Mapped[int]
    last_synced_month: Mapped[int]
    last_synced_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    player: Mapped[Player] = relationship(back_populates="sync_state")


class Analysis(Base):
    """Una corrida de análisis de motor sobre una partida (RF-2) o sobre la
    línea principal de un tablero de análisis (RF-6.9).

    Puede haber varias por partida (distinto motor, profundidad o MultiPV);
    por eso no es una columna más de `Game` sino su propia tabla.

    **Nunca cuelga de nada**: al menos una de las dos columnas está llena.
    `board_id` dice de qué tablero salieron las jugadas; `game_id`, a qué
    partida del historial se le atribuyen. Un análisis de partida solo tiene
    la segunda y uno de tablero solo la primera, salvo que el tablero esté
    publicado como partida propia (RF-6.5), donde tiene las dos: las jugadas
    son del tablero y cuentan como las de esa partida (ADR-0014).

    Son la misma corrida de motor sobre las mismas jugadas y dan el mismo
    resultado, así que compartir tabla evita duplicar `analyzed_moves` y todo
    lo que lee de ella (el visor, la exportación a PGN, los patrones).
    """

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id"), default=None)
    board_id: Mapped[int | None] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), default=None
    )
    """El tablero del que salieron las jugadas (RF-6.9).

    Por sí solo **no cuenta en las estadísticas** (RF-6.5): lo garantiza
    `latest_analysis_ids`, que solo mira los análisis con `game_id`. Un
    tablero publicado como partida propia lo llena además, y entonces sí
    cuenta (`services/own_games.py`)."""
    analyzed_pgn: Mapped[str | None] = mapped_column(default=None)
    """La línea principal que se analizó, solo para los tableros.

    Una partida no la necesita —su PGN está en `games.pgn` y no cambia—, pero
    un tablero se sigue editando después de analizarlo: guardar aquí lo que
    se analizó es lo que permite decir "este análisis es de una versión
    anterior" en vez de enseñar clasificaciones que ya no corresponden a las
    jugadas que hay en pantalla."""
    engine: Mapped[str]
    """"stockfish" | "lc0" (RF-2.6), o cualquier otro configurado en `EngineConfig`."""
    depth: Mapped[int]
    multipv: Mapped[int]
    status: Mapped[str] = mapped_column(default="queued")
    """"queued" | "running" | "done" | "error"."""
    error: Mapped[str | None] = mapped_column(default=None)
    white_accuracy: Mapped[float | None] = mapped_column(default=None)
    black_accuracy: Mapped[float | None] = mapped_column(default=None)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    game: Mapped[Game | None] = relationship(back_populates="analyses")
    moves: Mapped[list[AnalyzedMove]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="AnalyzedMove.ply",
    )


class AnalyzedMove(Base):
    """Una jugada ya evaluada y clasificada dentro de un `Analysis`
    (RF-2.2 / RF-2.3), tal como la produce `lucia_core.analysis.AnalyzedMove`."""

    __tablename__ = "analyzed_moves"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    """Con `CASCADE` en la base y no solo en la relación de SQLAlchemy: borrar
    un tablero se lleva sus análisis por la clave foránea, sin que el ORM los
    llegue a cargar, y entonces nadie recorrería la relación para borrar estas
    filas. Sin esto, borrar un tablero analizado falla."""
    ply: Mapped[int]
    color: Mapped[str]
    """"white" | "black": quién jugó esta jugada."""
    san: Mapped[str]
    uci: Mapped[str]
    fen_before: Mapped[str]
    classification: Mapped[str]
    """Una de `lucia_core.classification.MoveClassification`."""
    phase: Mapped[str] = mapped_column(default="middlegame")
    """"opening" | "middlegame" | "endgame" (RF-3.3), de `lucia_core.phases`."""
    move_accuracy: Mapped[float]
    win_percent_before: Mapped[float]
    win_percent_after: Mapped[float]
    best_move_uci: Mapped[str | None] = mapped_column(default=None)
    alternatives_json: Mapped[list | None] = mapped_column(JSON, default=None)
    """Las N mejores líneas de la posición **anterior** a esta jugada (RF-10.1),
    de mejor a peor: `[{rank, score_cp, score_mate, pv_uci}]`, con la puntuación
    desde el punto de vista de las blancas, como todo lo que se guarda.

    Es lo que permite al visor enseñar las alternativas de cada jugada, no solo
    `best_move_uci`. `None` en los análisis anteriores a RF-10; para esos, el
    router las recupera de `position_cache` cuando puede (ver
    `services/analysis.py::alternatives_from_cache`).

    La notación SAN no se guarda: depende de la posición y se deriva de
    `fen_before` al servir, para no almacenar dos veces la misma jugada.

    Por qué JSON aquí y no una tabla de líneas: ADR-0007."""

    analysis: Mapped[Analysis] = relationship(back_populates="moves")


class ExplorerPositionCache(Base):
    """Lo que la base de maestros de Lichess dice de una posición (RF-3.6).

    Es una caché, no una fuente: se guarda para no volver a preguntar por la
    misma posición —y para que comparar el repertorio siga funcionando sin
    conexión, que es la única concesión que LUCIA hace a RNF-1 (ver ADR-0010)—.

    La clave es el **EPD**, el FEN sin los contadores de jugada, por lo mismo
    que en `lucia_core.openings`: la misma posición alcanzada por otro orden de
    jugadas tiene la misma teoría detrás.
    """

    __tablename__ = "explorer_positions"

    epd: Mapped[str] = mapped_column(primary_key=True)
    masters_json: Mapped[dict] = mapped_column(JSON)
    """Respuesta del explorador, ya recortada a lo que se usa: totales de la
    posición y qué se juega en ella (`lucia_lichess.ExplorerPosition`)."""
    fetched_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    """Cuándo se preguntó. La base de maestros cambia despacio, así que no
    caduca sola; sirve para poder decidirlo más adelante sin migrar nada."""


class EngineSettings(Base):
    """Parámetros de análisis por motor, editables desde la UI (RF-5.4).

    **No** incluye la ruta del binario a propósito: permitir cambiarla por
    HTTP sería ejecución arbitraria de comandos desde el navegador. Las rutas
    siguen viniendo de `.env` y la API solo las expone en modo lectura.

    Una fila por motor; si no existe, valen los valores por defecto de
    `Settings` (ver `lucia_api.services.engines.get_effective_config`).
    """

    __tablename__ = "engine_settings"

    name: Mapped[str] = mapped_column(primary_key=True)
    """"stockfish" | "lc0"."""
    threads: Mapped[int]
    hash_mb: Mapped[int]
    depth: Mapped[int]
    multipv: Mapped[int]
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )


class Board(Base):
    """Tablero de análisis: partidas presenciales, posiciones de libro o
    ideas sueltas (RF-6).

    El árbol de variantes se guarda como JSON y la API **no lo interpreta**:
    quien sabe de reglas de ajedrez en el front es chess.js, y duplicar esa
    lógica en el servidor solo daría dos sitios donde equivocarse. El servidor
    lo trata como un documento que guarda y devuelve.

    Un tablero no cuenta para las estadísticas (RF-6.5) salvo que el usuario
    marque que esa partida la jugó él, y entonces se **publica al historial**
    como una fila de `games` a la que apunta `own_game_id`: así el dashboard,
    los filtros y los patrones lo cuentan sin que ninguna de sus consultas
    tenga que aprender qué es un tablero (ADR-0014).
    """

    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    tags_json: Mapped[list | None] = mapped_column(JSON, default=None)
    root_fen: Mapped[str]
    """Posición de partida del tablero: la inicial, un FEN pegado o una
    posición montada en el editor."""
    tree_json: Mapped[dict] = mapped_column(JSON)
    """Árbol de variantes con comentarios (ver `lucia_api.routers.boards`)."""
    own_game_id: Mapped[int | None] = mapped_column(
        ForeignKey("games.id", ondelete="SET NULL"), default=None
    )
    """La partida del historial en la que se publicó este tablero (RF-6.5), o
    `None` si no está marcado como partida propia.

    Es la **única** marca: un booleano aparte podría contradecir a la fila
    publicada, y entonces el listado diría una cosa y el dashboard otra.
    `SET NULL` porque borrar esa partida desde el historial es retirar la
    marca, no borrar el tablero."""
    current_version_id: Mapped[int | None] = mapped_column(default=None)
    """En qué punto del historial está el tablero (RF-6.8).

    No es "la última versión" sino "la que se está viendo": deshacer mueve
    este puntero hacia atrás sin borrar nada, y así rehacer puede volver.
    Guardarlo aquí y no en la pantalla es lo que hace que el deshacer
    sobreviva a recargar.

    Sin `ForeignKey` a propósito: `board_versions.board_id` ya apunta aquí, y
    declarar las dos direcciones deja un ciclo de tablas que SQLite no puede
    romper —no sabe añadir una restricción después de crear la tabla—. Las
    versiones se borran en cascada con su tablero, así que el puntero no
    puede quedar colgando.
    """
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )

    @property
    def is_own_game(self) -> bool:
        """Si el tablero está publicado como partida propia (RF-6.5).

        Se deduce del enlace en vez de guardarse aparte para que no haya dos
        versiones de la misma verdad. Las respuestas de la API lo exponen tal
        cual, así que el front sigue viendo el mismo campo de siempre."""
        return self.own_game_id is not None


class BoardVersion(Base):
    """Un estado por el que pasó un tablero de análisis (RF-6.8).

    El historial es **lineal**, como el de un editor de texto: se apunta con
    `Board.current_version_id` y editar después de deshacer borra lo que
    quedaba por delante. Un árbol de versiones sería más potente y mucho más
    difícil de explicar en una pantalla que ya tiene un árbol de variantes.

    Se guarda el árbol entero y no un diff: un tablero pesa unos kilobytes,
    y reconstruir un estado aplicando diferencias es la clase de código que
    falla justo cuando hace falta.
    """

    __tablename__ = "board_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    root_fen: Mapped[str]
    """Va con el árbol porque importar un PGN puede mover la posición de
    partida (RF-6.7): sin esto, deshacer una importación dejaría el árbol
    viejo colgando de la raíz nueva."""
    tree_json: Mapped[dict] = mapped_column(JSON)
    pgn: Mapped[str | None] = mapped_column(default=None)
    """El mismo árbol en PGN, tal como lo compuso el front (`tree.ts::toPgn`).

    Se guarda junto al árbol porque la API no sabe recorrerlo —quien sabe de
    jugadas es chess.js— y al deshacer hace falta: un tablero publicado como
    partida propia (RF-6.5) tiene que poner al día su fila del historial con
    las jugadas que quedaron, y sin esto habría que pedírselas a la pantalla
    en un segundo viaje. `None` en las versiones anteriores a RF-6.5 y en la
    primera de un tablero recién creado, donde no se sabe cómo quedó: ahí el
    análisis se desenlaza hasta el siguiente guardado."""
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )


class PositionCache(Base):
    """Caché de evaluaciones por FEN (RF-2.7): aperturas y posiciones
    repetidas entre partidas no se le vuelven a preguntar al motor.

    Clave compuesta por posición **y** configuración del motor: la misma
    posición evaluada a otra profundidad, otro MultiPV o con otro motor no es
    intercambiable, así que no comparte fila.
    """

    __tablename__ = "position_cache"

    fen: Mapped[str] = mapped_column(primary_key=True)
    engine: Mapped[str] = mapped_column(primary_key=True)
    depth: Mapped[int] = mapped_column(primary_key=True)
    multipv: Mapped[int] = mapped_column(primary_key=True)
    lines_json: Mapped[list] = mapped_column(JSON)
    """Una entrada por línea de MultiPV, ver
    `lucia_api.services.analysis._serialize_line`."""
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )


class Puzzle(Base):
    """Un puzzle sacado de un error propio, con su estado de repaso (RF-4.1).

    La posición es la de **antes** del error y quien resuelve es quien lo
    cometió: el turno del FEN ya lo dice, así que no hace falta guardar el
    color aparte.

    **Se guarda entero y no como un enlace a la jugada analizada.** Volver a
    analizar la partida —con otro motor o a otra profundidad— escribe un
    `Analysis` nuevo con sus propias `analyzed_moves`, y la fila de la que
    salió el puzzle deja de ser la vigente; borrar ese análisis se la lleva en
    cascada. Con un `analyzed_move_id` por delante, el puzzle se quedaría
    colgando de una fila obsoleta o desaparecida, y con ella se iría el
    historial de repasos, que es justo lo que no se puede perder: un puzzle
    acertado tres veces vale por esas tres veces, no por la fila que lo
    originó. Lo que sí lo identifica es de dónde salió, y por eso la clave
    única es la partida y la jugada: reanalizar no crea un puzzle repetido.
    Razonado en ADR-0017.
    """

    __tablename__ = "puzzles"
    __table_args__ = (UniqueConstraint("game_id", "ply", name="uq_puzzle_game_ply"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    """La partida donde se cometió el error. En cascada: borrada la partida, el
    puzzle no se puede volver a situar ni revisar, así que se va con ella."""
    ply: Mapped[int]

    fen: Mapped[str]
    """La posición a resolver: la de antes del error."""
    played_uci: Mapped[str]
    """Lo que se jugó de verdad. **No se manda a la pantalla hasta que el
    puzzle se cierra**: verlo antes es media solución."""
    solutions_json: Mapped[list] = mapped_column(JSON)
    """Las jugadas que se aceptan como respuesta, en UCI y de mejor a peor
    (RF-10.3, `lucia_core.training.equivalent_solutions`). La primera es la
    del motor; las demás son las que pierden lo mismo que ella.

    Se congela al generar el puzzle y no se recalcula al servirlo: el puzzle
    es el que era cuando se generó, y cambiar sus respuestas bajo un historial
    de repasos ya hecho falsearía ese historial."""
    classification: Mapped[str]
    """Qué fue el error, de `lucia_core.classification`: "blunder", "mistake" o
    "missed_win". Es lo que la pantalla enseña al cerrar el puzzle, con la
    misma insignia que el visor (criterio C-5)."""
    win_percent_before: Mapped[float]
    win_percent_after: Mapped[float]
    """Probabilidad de victoria **de quien resuelve**, antes y después del
    error: lo que costó, dicho en la unidad de siempre (RF-2.3)."""

    repetitions: Mapped[int] = mapped_column(default=0)
    interval_days: Mapped[int] = mapped_column(default=0)
    ease_factor: Mapped[float] = mapped_column(default=2.5)
    """El estado de SM-2 (`lucia_core.training.SpacedRepetitionState`), una
    columna por campo para poder ordenar y filtrar por él en SQL."""
    due_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC), index=True
    )
    """Cuándo vuelve a tocar. Un puzzle recién generado toca ya. Indexada
    porque la cola de repaso se pide siempre por ella."""
    last_reviewed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )

    game: Mapped[Game] = relationship()


class SparringGame(Base):
    """Una partida jugada contra el motor con fuerza calibrada (RF-4.3).

    **Guarda lo mínimo del que todo lo demás se deriva**: la posición de
    partida y las jugadas en UCI, en orden. La posición actual, el PGN y si la
    partida acabó se recalculan al vuelo con `lucia_core.sparring`, así que no
    pueden contradecirse entre sí — es la misma razón por la que un tablero no
    guarda su posición actual aparte del árbol.

    **No es una `Game` del historial** y no cuenta en estadísticas ni en
    detección de patrones (RF-3), igual que un tablero de análisis sin
    publicar (RF-6.5): una partida contra un motor al que se le ha bajado la
    fuerza no dice nada del rendimiento real. Para analizarla se abre como
    tablero de análisis (RF-6.6), que es el camino que ya existe y que deja el
    análisis fuera de las estadísticas por construcción.
    """

    __tablename__ = "sparring_games"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_color: Mapped[str]
    """"white" | "black": de qué color juega la persona. El motor lleva el otro."""
    engine: Mapped[str]
    """"stockfish" | "lc0", el rival."""
    engine_elo: Mapped[int | None] = mapped_column(default=None)
    """Fuerza pedida con `UCI_Elo`. **Solo Stockfish**: Lc0 juega con una red
    Maia, cuya fuerza es la de la red que se cargó y no un número que se le
    pueda pedir, así que ahí queda a `None` (ver `services/sparring.py`)."""
    starting_fen: Mapped[str]
    """Hoy siempre la inicial. Está en columna y no dado por supuesto porque
    RF-4.4 ("re-juega desde el error") y RF-11.1 arrancan de otra posición, y
    entonces no habría que migrar nada."""
    moves_uci_json: Mapped[list] = mapped_column(JSON, default=list)
    """Las jugadas de la partida, en UCI y en orden, las de ambos bandos."""

    result: Mapped[str | None] = mapped_column(default=None)
    """"1-0" | "0-1" | "1/2-1/2", o `None` mientras se juega.

    Es la **única** marca de que la partida terminó: un booleano aparte podría
    contradecirla. `termination` dice por qué (`lucia_core.sparring`)."""
    termination: Mapped[str | None] = mapped_column(default=None)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    """Cuándo se jugó la última jugada. Ordena el listado: lo que se está
    jugando ahora va primero."""

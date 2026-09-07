"""Modelo de datos de LUCIA (ver docs/03-arquitectura.md § Modelo de datos).

RF-1 (importación desde chess.com): `Player`, `Game`, `SyncState`.
RF-2 (análisis con motores): `Analysis`, `AnalyzedMove`, `PositionCache`.
"""

from __future__ import annotations

import datetime as dt

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


class SyncState(Base):
    """Progreso de sincronización incremental por jugador (RF-1.3)."""

    __tablename__ = "sync_state"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    last_synced_year: Mapped[int]
    last_synced_month: Mapped[int]
    last_synced_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    player: Mapped[Player] = relationship(back_populates="sync_state")


class Analysis(Base):
    """Una corrida de análisis de motor sobre una partida (RF-2).

    Puede haber varias por partida (distinto motor, profundidad o MultiPV);
    por eso no es una columna más de `Game` sino su propia tabla.
    """

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
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

    game: Mapped[Game] = relationship(back_populates="analyses")
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
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"))
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

    analysis: Mapped[Analysis] = relationship(back_populates="moves")


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

    `is_own_game` existe por RF-6.5: los tableros no cuentan para las
    estadísticas salvo que el usuario marque que esa partida la jugó él.
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
    is_own_game: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
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

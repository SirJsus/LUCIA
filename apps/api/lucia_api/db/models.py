"""Modelo de datos de LUCIA (ver docs/03-arquitectura.md § Modelo de datos).

Solo lo que necesita RF-1 (importación desde chess.com) por ahora: `Player`,
`Game` y `SyncState`. Las tablas de análisis (`analyses`, `analyzed_moves`,
`position_cache`) llegan con RF-2.
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


class SyncState(Base):
    """Progreso de sincronización incremental por jugador (RF-1.3)."""

    __tablename__ = "sync_state"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    last_synced_year: Mapped[int]
    last_synced_month: Mapped[int]
    last_synced_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    player: Mapped[Player] = relationship(back_populates="sync_state")

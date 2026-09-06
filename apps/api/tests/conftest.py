"""Fixtures compartidas: base de datos temporal por test y un
`ChessComClient` falso que no toca la red."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest
import pytest_asyncio
from lucia_api.db.base import Base
from lucia_chesscom import ChessComGame, ChessComPlayer, ChessComPlayerStats
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def db_session(tmp_path: Path) -> AsyncIterator[AsyncSession]:
    """Una base SQLite de usar y tirar por test, con el esquema real
    (mismos modelos que produce Alembic), sin tocar `data/lucia.db`."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def game_factory() -> Callable[..., ChessComGame]:
    """Fábrica de `ChessComGame` de prueba, expuesta como fixture (no como
    import directo) para no depender de que `tests` sea un paquete
    importable — hay un `tests/` por cada miembro del workspace y
    `--import-mode=importlib` evita justamente esa colisión."""
    return _make_game


def _make_game(
    *,
    uuid: str,
    white: str = "jugador_blanco",
    black: str = "jugador_negro",
    end_time: int = 1_700_000_000,
    pgn: str | None = None,
) -> ChessComGame:
    """Construye una `ChessComGame` de prueba con los campos mínimos que usa
    `sync_player`, sin depender de una respuesta real de chess.com."""
    return ChessComGame.model_validate(
        {
            "url": f"https://www.chess.com/game/live/{uuid}",
            "uuid": uuid,
            "pgn": pgn or _pgn_de_ejemplo(white, black),
            "time_control": "600",
            "end_time": end_time,
            "rated": True,
            "time_class": "rapid",
            "rules": "chess",
            "eco": "https://www.chess.com/openings/Italian-Game",
            "white": {"username": white, "rating": 1500, "result": "win"},
            "black": {"username": black, "rating": 1480, "result": "checkmated"},
        }
    )


def _pgn_de_ejemplo(white: str, black: str) -> str:
    return (
        f'[White "{white}"]\n[Black "{black}"]\n[Result "1-0"]\n\n'
        "1. e4 {[%clk 0:09:58.1]} 1... e5 {[%clk 0:09:57.5]} 1-0\n"
    )


@pytest.fixture
def fake_chesscom_client() -> Callable[..., FakeChessComClient]:
    """Constructor de `FakeChessComClient`, expuesto como fixture por la
    misma razón que `game_factory` (ver arriba)."""
    return FakeChessComClient


class FakeChessComClient:
    """Doble de `ChessComClient` para tests: sin red, datos fijados a mano."""

    def __init__(
        self,
        archives: list[tuple[int, int]],
        games_by_month: dict[tuple[int, int], list[ChessComGame]],
    ) -> None:
        self._archives = archives
        self._games_by_month = games_by_month

    async def get_player(self, username: str) -> ChessComPlayer:
        return ChessComPlayer.model_validate(
            {
                "username": username,
                "player_id": 1,
                "country": "https://api.chess.com/pub/country/MX",
                "joined": 1_600_000_000,
            }
        )

    async def get_stats(self, username: str) -> ChessComPlayerStats:
        return ChessComPlayerStats.model_validate(
            {"chess_rapid": {"last": {"rating": 1500, "date": 0, "rd": 50}}}
        )

    async def get_archives(self, username: str) -> list[tuple[int, int]]:
        return self._archives

    async def get_month_games(self, username: str, year: int, month: int) -> list[ChessComGame]:
        return self._games_by_month.get((year, month), [])

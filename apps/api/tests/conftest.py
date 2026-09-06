"""Fixtures compartidas: base de datos temporal por test y un
`ChessComClient` falso que no toca la red."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from lucia_api.db.base import Base
from lucia_chesscom import ChessComGame, ChessComPlayer, ChessComPlayerStats
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# packages/core/tests/conftest.py -> tests -> api -> apps -> raíz del repo.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
STOCKFISH_PATH = _PROJECT_ROOT / "engines" / "bin" / "stockfish"

requiere_stockfish = pytest.mark.skipif(
    not STOCKFISH_PATH.exists(),
    reason="Stockfish no está compilado; ejecuta 'make engines' para correr estos tests.",
)


@pytest.fixture(autouse=True)
def _worker_limpio() -> Iterator[None]:
    """`app` es un singleton de módulo compartido entre tests. Sin esto, el
    segundo test que entra a `TestClient(app)` heredaría el `AnalysisWorker`
    (y su `asyncio.Queue`) del test anterior, atado a un event loop ya
    cerrado — pytest-asyncio crea uno nuevo por test. Se limpia antes y
    después de cada test para que `lifespan()` siempre cree uno propio,
    salvo que el test mismo fije `app.state.worker` tras este fixture."""
    from lucia_api.main import app

    if hasattr(app.state, "worker"):
        del app.state.worker
    yield
    if hasattr(app.state, "worker"):
        del app.state.worker


@pytest_asyncio.fixture
async def db_engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    """El motor SQLite de usar y tirar por test, con el esquema real (mismos
    modelos que produce Alembic), sin tocar `data/lucia.db`. Expuesto aparte
    de `db_session` para que el worker en background pueda tener su propia
    fábrica de sesiones apuntando a la misma base temporal (ver
    `db_session_factory`), tal como pasa en producción con `data/lucia.db`."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def db_session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with db_session_factory() as session:
        yield session


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

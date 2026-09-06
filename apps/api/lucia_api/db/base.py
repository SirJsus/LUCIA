"""Motor y sesión de base de datos (SQLite local-first, ver ADR-0005).

`ensure_sqlite_dir()` existe porque sqlite crea el archivo de base de datos
pero no los directorios intermedios: sin esto, un `data/` inexistente hace
fallar la primera conexión en un clon nuevo del repo.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from lucia_api.settings import settings


class Base(DeclarativeBase):
    pass


def ensure_sqlite_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite"):
        return
    path_part = database_url.split("///", 1)[-1]
    if path_part in (":memory:", ""):
        return
    Path(path_part).parent.mkdir(parents=True, exist_ok=True)


ensure_sqlite_dir(settings.database_url)
engine = create_async_engine(settings.database_url)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por request."""
    async with async_session_factory() as session:
        yield session

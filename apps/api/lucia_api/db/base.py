"""Motor y sesión de base de datos (SQLite local-first, ver ADR-0005).

Todo el que abra una conexión a la base pasa por `create_db_engine`, y no por
`create_async_engine` a secas, porque hay dos cosas que hay que hacer siempre y
que sqlite no hace solo:

- **Crear los directorios intermedios** (`ensure_sqlite_dir`): sqlite crea el
  archivo de base de datos pero no la carpeta que lo contiene, así que un
  `data/` inexistente hace fallar la primera conexión en un clon nuevo.
- **Encender las claves foráneas** (`PRAGMA foreign_keys=ON`): en sqlite vienen
  **apagadas** por conexión, de modo que sin esto ningún `ON DELETE` del
  esquema se ejecuta. Borrar un tablero dejaba sus análisis
  (`analyses.board_id`, ADR-0013) y sus versiones (`board_versions.board_id`,
  ADR-0012) colgando en la base, que es justo lo que esos dos ADR dan por
  hecho que no pasa.

Las migraciones son la excepción y **no** encienden el pragma: alembic recrea
tablas enteras para cambiarlas en sqlite (`batch_alter_table`), y con las
claves foráneas encendidas ese renombrado se lleva por delante lo que apunta a
la tabla que está recreando.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
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


def create_db_engine(database_url: str) -> AsyncEngine:
    """El motor con el que habla toda la aplicación, y también los tests.

    Existe para que nadie tenga que acordarse del pragma: una conexión sqlite
    sin él ignora en silencio los `ON DELETE` del esquema, y el fallo no se ve
    hasta que alguien mira la base y encuentra filas de un tablero que ya no
    existe.
    """
    ensure_sqlite_dir(database_url)
    engine = create_async_engine(database_url)
    if engine.url.get_backend_name() != "sqlite":
        return engine

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
        # Una vez por conexión, no por sesión: el pragma es de la conexión y
        # el pool las reutiliza.
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_db_engine(settings.database_url)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por request."""
    async with async_session_factory() as session:
        yield session

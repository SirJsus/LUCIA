from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.main import app
from lucia_api.services.engines import get_effective_config
from sqlalchemy.ext.asyncio import AsyncSession


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_engines_config_reporta_rutas_y_disponibilidad(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.get("/engines/config")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    body = respuesta.json()
    assert body["stockfish"]["name"] == "stockfish"
    assert isinstance(body["stockfish"]["available"], bool)
    assert isinstance(body["lc0"]["weights_available"], bool)
    assert body["stockfish"]["weights_path"] is None  # solo Lc0 usa red


async def test_put_actualiza_y_persiste_la_configuracion(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.put(
                "/engines/config/stockfish",
                json={"threads": 4, "hash_mb": 512, "depth": 20, "multipv": 5},
            )
            assert respuesta.status_code == 200, respuesta.text
            assert respuesta.json()["threads"] == 4

            # Vuelve a leerse desde la BD, no solo del eco del PUT.
            leida = http.get("/engines/config").json()["stockfish"]
            assert leida["threads"] == 4
            assert leida["hash_mb"] == 512
            assert leida["depth"] == 20
            assert leida["multipv"] == 5
    finally:
        app.dependency_overrides.clear()

    config = await get_effective_config(db_session, "stockfish")
    assert config.depth == 20


async def test_put_no_permite_cambiar_la_ruta_del_binario(db_session: AsyncSession) -> None:
    """La ruta es de solo lectura a propósito: aceptarla por HTTP sería
    ejecución arbitraria de comandos desde el navegador."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            antes = http.get("/engines/config").json()["stockfish"]["path"]
            http.put(
                "/engines/config/stockfish",
                json={
                    "threads": 2,
                    "hash_mb": 256,
                    "depth": 18,
                    "multipv": 3,
                    "path": "/bin/sh",  # campo extra: debe ignorarse
                },
            )
            despues = http.get("/engines/config").json()["stockfish"]["path"]
    finally:
        app.dependency_overrides.clear()

    assert despues == antes
    assert "/bin/sh" not in despues


async def test_put_rechaza_valores_fuera_de_rango(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            demasiados_hilos = http.put(
                "/engines/config/stockfish",
                json={"threads": 999, "hash_mb": 256, "depth": 18, "multipv": 3},
            )
            profundidad_absurda = http.put(
                "/engines/config/stockfish",
                json={"threads": 2, "hash_mb": 256, "depth": 100, "multipv": 3},
            )
    finally:
        app.dependency_overrides.clear()

    assert demasiados_hilos.status_code == 422
    assert profundidad_absurda.status_code == 422


async def test_put_a_motor_desconocido_da_404(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.put(
                "/engines/config/komodo",
                json={"threads": 2, "hash_mb": 256, "depth": 18, "multipv": 3},
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 404

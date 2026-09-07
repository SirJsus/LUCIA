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


async def test_engines_config_reports_paths_and_availability(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/engines/config")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["stockfish"]["name"] == "stockfish"
    assert isinstance(body["stockfish"]["available"], bool)
    assert isinstance(body["lc0"]["weights_available"], bool)
    assert body["stockfish"]["weights_path"] is None  # solo Lc0 usa red


async def test_put_updates_and_persists_the_config(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.put(
                "/engines/config/stockfish",
                json={"threads": 4, "hash_mb": 512, "depth": 20, "multipv": 5},
            )
            assert response.status_code == 200, response.text
            assert response.json()["threads"] == 4

            # Vuelve a leerse desde la BD, no solo del eco del PUT.
            stored_config = http.get("/engines/config").json()["stockfish"]
            assert stored_config["threads"] == 4
            assert stored_config["hash_mb"] == 512
            assert stored_config["depth"] == 20
            assert stored_config["multipv"] == 5
    finally:
        app.dependency_overrides.clear()

    config = await get_effective_config(db_session, "stockfish")
    assert config.depth == 20


async def test_put_does_not_allow_changing_the_binary_path(db_session: AsyncSession) -> None:
    """La ruta es de solo lectura a propósito: aceptarla por HTTP sería
    ejecución arbitraria de comandos desde el navegador."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            path_before = http.get("/engines/config").json()["stockfish"]["path"]
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
            path_after = http.get("/engines/config").json()["stockfish"]["path"]
    finally:
        app.dependency_overrides.clear()

    assert path_after == path_before
    assert "/bin/sh" not in path_after


async def test_put_rejects_out_of_range_values(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            too_many_threads = http.put(
                "/engines/config/stockfish",
                json={"threads": 999, "hash_mb": 256, "depth": 18, "multipv": 3},
            )
            absurd_depth = http.put(
                "/engines/config/stockfish",
                json={"threads": 2, "hash_mb": 256, "depth": 100, "multipv": 3},
            )
    finally:
        app.dependency_overrides.clear()

    assert too_many_threads.status_code == 422
    assert absurd_depth.status_code == 422


async def test_put_to_an_unknown_engine_returns_404(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.put(
                "/engines/config/komodo",
                json={"threads": 2, "hash_mb": 256, "depth": 18, "multipv": 3},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


async def test_lc0_accepts_thousands_of_nodes_and_stockfish_does_not(
    db_session: AsyncSession,
) -> None:
    """El mismo campo significa profundidad en Stockfish y nodos en Lc0, así
    que el rango válido no puede ser el mismo: 1600 es una profundidad
    imposible y un número de nodos normal."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            lc0_response = http.put(
                "/engines/config/lc0",
                json={"threads": 2, "hash_mb": 256, "depth": 1600, "multipv": 1},
            )
            stockfish_response = http.put(
                "/engines/config/stockfish",
                json={"threads": 2, "hash_mb": 256, "depth": 1600, "multipv": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert lc0_response.status_code == 200, lc0_response.text
    assert lc0_response.json()["depth"] == 1600
    assert stockfish_response.status_code == 422
    assert "depth" in stockfish_response.json()["detail"]

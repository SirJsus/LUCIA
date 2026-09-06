"""Tablero de análisis (RF-6): CRUD y análisis de una posición suelta."""

from __future__ import annotations

from collections.abc import AsyncIterator

import chess
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.main import app
from sqlalchemy.ext.asyncio import AsyncSession

from .conftest import requiere_stockfish

ARBOL_EJEMPLO = {
    "id": "root",
    "san": None,
    "children": [{"id": "n1", "san": "e4", "uci": "e2e4", "children": []}],
}


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_ciclo_completo_crear_leer_actualizar_borrar(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            creado = http.post(
                "/boards",
                json={"title": "Mi partida OTB", "tree_json": ARBOL_EJEMPLO},
            )
            assert creado.status_code == 201, creado.text
            board_id = creado.json()["id"]
            assert creado.json()["root_fen"] == chess.STARTING_FEN
            assert creado.json()["is_own_game"] is False

            leido = http.get(f"/boards/{board_id}").json()
            assert leido["tree_json"] == ARBOL_EJEMPLO

            # Autoguardado: se manda solo lo que cambió.
            actualizado = http.put(
                f"/boards/{board_id}",
                json={"title": "Mi partida OTB (revisada)", "is_own_game": True},
            )
            assert actualizado.status_code == 200
            assert actualizado.json()["title"] == "Mi partida OTB (revisada)"
            assert actualizado.json()["is_own_game"] is True
            assert actualizado.json()["tree_json"] == ARBOL_EJEMPLO  # no se pisa

            assert len(http.get("/boards").json()) == 1

            assert http.delete(f"/boards/{board_id}").status_code == 204
            assert http.get(f"/boards/{board_id}").status_code == 404
            assert http.get("/boards").json() == []
    finally:
        app.dependency_overrides.clear()


async def test_crear_desde_un_fen(db_session: AsyncSession) -> None:
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.post("/boards", json={"title": "Italiana", "root_fen": fen})
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 201
    assert respuesta.json()["root_fen"] == fen


async def test_fen_invalido_se_rechaza_al_crear(db_session: AsyncSession) -> None:
    """Guardar un FEN ilegal daría un tablero imposible de abrir después."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.post(
                "/boards", json={"title": "Roto", "root_fen": "esto no es un fen"}
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 422


async def test_actualizar_o_borrar_un_tablero_inexistente_da_404(
    db_session: AsyncSession,
) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            assert http.put("/boards/9999", json={"title": "x"}).status_code == 404
            assert http.delete("/boards/9999").status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_position_no_se_confunde_con_un_id_de_analisis(db_session: AsyncSession) -> None:
    """`/analysis/position` se declara antes que `/analysis/{analysis_id}`; si
    se invirtieran, FastAPI intentaría interpretar "position" como un entero."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.post("/analysis/position", json={"fen": "no-es-un-fen"})
    finally:
        app.dependency_overrides.clear()

    # 422 por FEN inválido, no 404 ni un error de tipo de ruta.
    assert respuesta.status_code == 422
    assert "FEN" in respuesta.json()["detail"]


@requiere_stockfish
async def test_analiza_una_posicion_y_devuelve_lineas(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.post(
                "/analysis/position",
                json={"fen": chess.STARTING_FEN, "depth": 8, "multipv": 2},
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200, respuesta.text
    lineas = respuesta.json()
    assert len(lineas) == 2
    assert lineas[0]["rank"] == 1
    assert lineas[0]["pv_uci"]  # hay al menos una jugada propuesta
    assert lineas[0]["pv_san"][0] in {"e4", "d4", "Nf3", "c4", "g3", "b3", "e3"}
    # La posición inicial está equilibrada: no debe haber mate.
    assert lineas[0]["score_mate"] is None


@requiere_stockfish
async def test_detecta_mate_en_una_posicion_forzada(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.post(
                "/analysis/position",
                json={"fen": "6k1/5ppp/8/8/8/8/8/4R2K w - - 0 1", "depth": 10, "multipv": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.json()[0]["score_mate"] == 1


async def test_profundidad_excesiva_se_rechaza(db_session: AsyncSession) -> None:
    """El análisis en vivo es síncrono: sin tope, la petición quedaría colgada."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.post(
                "/analysis/position", json={"fen": chess.STARTING_FEN, "depth": 40}
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 422

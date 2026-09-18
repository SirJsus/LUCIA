"""Tablero de análisis (RF-6): CRUD y análisis de una posición suelta."""

from __future__ import annotations

from collections.abc import AsyncIterator

import chess
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.main import app
from sqlalchemy.ext.asyncio import AsyncSession

from .conftest import requires_stockfish

SAMPLE_TREE = {
    "id": "root",
    "san": None,
    "children": [{"id": "n1", "san": "e4", "uci": "e2e4", "children": []}],
}


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_full_cycle_create_read_update_delete(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            created = http.post(
                "/boards",
                json={"title": "Mi partida OTB", "tree_json": SAMPLE_TREE},
            )
            assert created.status_code == 201, created.text
            board_id = created.json()["id"]
            assert created.json()["root_fen"] == chess.STARTING_FEN
            assert created.json()["is_own_game"] is False

            fetched = http.get(f"/boards/{board_id}").json()
            assert fetched["tree_json"] == SAMPLE_TREE

            # Autoguardado: se manda solo lo que cambió.
            updated = http.put(
                f"/boards/{board_id}",
                json={"title": "Mi partida OTB (revisada)", "is_own_game": True},
            )
            assert updated.status_code == 200
            assert updated.json()["title"] == "Mi partida OTB (revisada)"
            assert updated.json()["is_own_game"] is True
            assert updated.json()["tree_json"] == SAMPLE_TREE  # no se pisa

            assert len(http.get("/boards").json()) == 1

            assert http.delete(f"/boards/{board_id}").status_code == 204
            assert http.get(f"/boards/{board_id}").status_code == 404
            assert http.get("/boards").json() == []
    finally:
        app.dependency_overrides.clear()


async def test_create_from_a_fen(db_session: AsyncSession) -> None:
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/boards", json={"title": "Italiana", "root_fen": fen})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["root_fen"] == fen


async def test_invalid_fen_is_rejected_on_create(db_session: AsyncSession) -> None:
    """Guardar un FEN ilegal daría un tablero imposible de abrir después."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/boards", json={"title": "Roto", "root_fen": "esto no es un fen"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def test_update_or_delete_unknown_board_returns_404(
    db_session: AsyncSession,
) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            assert http.put("/boards/9999", json={"title": "x"}).status_code == 404
            assert http.delete("/boards/9999").status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_position_is_not_mistaken_for_an_analysis_id(db_session: AsyncSession) -> None:
    """`/analysis/position` se declara antes que `/analysis/{analysis_id}`; si
    se invirtieran, FastAPI intentaría interpretar "position" como un entero."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/analysis/position", json={"fen": "no-es-un-fen"})
    finally:
        app.dependency_overrides.clear()

    # 422 por FEN inválido, no 404 ni un error de tipo de ruta.
    assert response.status_code == 422
    assert "FEN" in response.json()["detail"]


@requires_stockfish
async def test_analyzes_a_position_and_returns_lines(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis/position",
                json={"fen": chess.STARTING_FEN, "depth": 8, "multipv": 2},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    lines = response.json()
    assert len(lines) == 2
    assert lines[0]["rank"] == 1
    assert lines[0]["pv_uci"]  # hay al menos una jugada propuesta
    assert lines[0]["pv_san"][0] in {"e4", "d4", "Nf3", "c4", "g3", "b3", "e3"}
    # La posición inicial está equilibrada: no debe haber mate.
    assert lines[0]["score_mate"] is None


@requires_stockfish
async def test_detects_mate_in_a_forced_position(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis/position",
                json={"fen": "6k1/5ppp/8/8/8/8/8/4R2K w - - 0 1", "depth": 10, "multipv": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.json()[0]["score_mate"] == 1


async def test_a_finished_position_is_not_sent_to_the_engine(db_session: AsyncSession) -> None:
    """Jaque mate y ahogado devuelven la lista vacía **sin abrir el motor**.

    No lleva `@requires_stockfish` a propósito: que pase sin motor compilado es
    justo la prueba de que no se abre ninguno. Preguntarle a Lc0 en una
    posición sin jugadas legales devuelve `bestmove a1a1`, que no es UCI
    válido y aborta la conexión; antes de la guarda, llegar al final de una
    partida terminada en mate en el tablero de análisis rompía el motor.
    """
    _override(db_session)
    checkmate = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    stalemate = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    try:
        with TestClient(app) as http:
            responses = [
                http.post("/analysis/position", json={"fen": fen})
                for fen in (checkmate, stalemate)
            ]
    finally:
        app.dependency_overrides.clear()

    for response in responses:
        assert response.status_code == 200, response.text
        assert response.json() == []


async def test_excessive_depth_is_rejected(db_session: AsyncSession) -> None:
    """El análisis en vivo es síncrono: sin tope, la petición quedaría colgada."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis/position", json={"fen": chess.STARTING_FEN, "depth": 40}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

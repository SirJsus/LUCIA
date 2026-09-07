"""Flujo completo de análisis a través de la API: POST /analysis encola el
trabajo, el worker real lo procesa contra Stockfish real, y el progreso llega
por WebSocket. Es el test "en vivo" de todo el bloque RF-2 en la API."""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Game, Player
from lucia_api.main import app
from lucia_api.worker import AnalysisWorker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .conftest import requires_stockfish

PGN = '[White "a"]\n[Black "b"]\n[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'


async def _create_game(session: AsyncSession) -> int:
    player = Player(platform="chesscom", username="prueba")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id="partida-api-1",
        pgn=PGN,
        white_username="a",
        white_rating=1000,
        white_result="checkmated",
        black_username="b",
        black_rating=1000,
        black_result="win",
        time_control="600",
        time_class="rapid",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2024,
        month=1,
    )
    session.add(game)
    await session.commit()
    return game.id


@requires_stockfish
async def test_full_flow_post_analysis_and_progress_websocket(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    game_id = await _create_game(db_session)

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    # El worker necesita su propia sesión por job (no puede compartir la del
    # request), pero debe leer y escribir en la MISMA base temporal que usa
    # el test — por eso se le da la fábrica, no una sesión ya abierta.
    app.state.worker = AnalysisWorker(session_factory=db_session_factory)

    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis", json={"game_ids": [game_id], "engine": "stockfish", "depth": 8}
            )
            assert response.status_code == 200, response.text
            analysis_id = response.json()[0]["id"]
            assert response.json()[0]["status"] == "queued"

            events = []
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                while True:
                    event = ws.receive_json()
                    events.append(event)
                    if event["status"] in ("done", "error"):
                        break

            assert events[-1]["status"] == "done"
            assert any(e["status"] == "running" for e in events)

            detail = http.get(f"/analysis/{analysis_id}").json()
            assert detail["status"] == "done"
            assert len(detail["moves"]) == 4
            assert detail["moves"][2]["uci"] == "g2g4"
            assert detail["white_accuracy"] < 90
    finally:
        app.dependency_overrides.clear()


@requires_stockfish
async def test_websocket_connecting_after_the_end_receives_the_final_result(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    game_id = await _create_game(db_session)

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    app.state.worker = AnalysisWorker(session_factory=db_session_factory)

    try:
        with TestClient(app) as http:
            response = http.post("/analysis", json={"game_ids": [game_id], "depth": 8})
            analysis_id = response.json()[0]["id"]

            # Deja que el worker termine antes de conectar el WebSocket.
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                while ws.receive_json()["status"] not in ("done", "error"):
                    pass

            # Segunda conexión, ya con el análisis terminado: debe recibir
            # el resultado final de una sola vez, sin esperar progreso.
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                event = ws.receive_json()
                assert event["status"] == "done"
    finally:
        app.dependency_overrides.clear()


async def test_post_analysis_with_unknown_game_id_returns_404(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.post("/analysis", json={"game_ids": [999999]})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_post_analysis_without_game_ids_returns_422(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.post("/analysis", json={"game_ids": []})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


async def test_get_analysis_with_unknown_id_returns_404(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.get("/analysis/999999")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()

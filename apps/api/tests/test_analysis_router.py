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

from .conftest import requiere_stockfish

PGN = '[White "a"]\n[Black "b"]\n[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'


async def _crear_partida(session: AsyncSession) -> int:
    jugador = Player(platform="chesscom", username="prueba")
    session.add(jugador)
    await session.flush()
    partida = Game(
        player_id=jugador.id,
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
    session.add(partida)
    await session.commit()
    return partida.id


@requiere_stockfish
async def test_flujo_completo_post_analysis_y_websocket_de_progreso(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    game_id = await _crear_partida(db_session)

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    # El worker necesita su propia sesión por job (no puede compartir la del
    # request), pero debe leer y escribir en la MISMA base temporal que usa
    # el test — por eso se le da la fábrica, no una sesión ya abierta.
    app.state.worker = AnalysisWorker(session_factory=db_session_factory)

    try:
        with TestClient(app) as http:
            respuesta = http.post(
                "/analysis", json={"game_ids": [game_id], "engine": "stockfish", "depth": 8}
            )
            assert respuesta.status_code == 200, respuesta.text
            analysis_id = respuesta.json()[0]["id"]
            assert respuesta.json()[0]["status"] == "queued"

            eventos = []
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                while True:
                    evento = ws.receive_json()
                    eventos.append(evento)
                    if evento["status"] in ("done", "error"):
                        break

            assert eventos[-1]["status"] == "done"
            assert any(e["status"] == "running" for e in eventos)

            detalle = http.get(f"/analysis/{analysis_id}").json()
            assert detalle["status"] == "done"
            assert len(detalle["moves"]) == 4
            assert detalle["moves"][2]["uci"] == "g2g4"
            assert detalle["white_accuracy"] < 90
    finally:
        app.dependency_overrides.clear()


@requiere_stockfish
async def test_websocket_conecta_despues_de_terminado_recibe_resultado_final(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    game_id = await _crear_partida(db_session)

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    app.state.worker = AnalysisWorker(session_factory=db_session_factory)

    try:
        with TestClient(app) as http:
            respuesta = http.post("/analysis", json={"game_ids": [game_id], "depth": 8})
            analysis_id = respuesta.json()[0]["id"]

            # Deja que el worker termine antes de conectar el WebSocket.
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                while ws.receive_json()["status"] not in ("done", "error"):
                    pass

            # Segunda conexión, ya con el análisis terminado: debe recibir
            # el resultado final de una sola vez, sin esperar progreso.
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                evento = ws.receive_json()
                assert evento["status"] == "done"
    finally:
        app.dependency_overrides.clear()


async def test_post_analysis_con_game_id_inexistente_da_404(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.post("/analysis", json={"game_ids": [999999]})
        assert respuesta.status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_post_analysis_sin_game_ids_da_422(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.post("/analysis", json={"game_ids": []})
        assert respuesta.status_code == 422
    finally:
        app.dependency_overrides.clear()


async def test_get_analysis_inexistente_da_404(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.get("/analysis/999999")
        assert respuesta.status_code == 404
    finally:
        app.dependency_overrides.clear()

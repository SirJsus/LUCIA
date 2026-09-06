from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Game, Player
from lucia_api.main import app
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "a"]\n[Black "b"]\n[Result "1-0"]\n\n1. e4 e5 1-0\n'


async def _crear_partida(
    session: AsyncSession,
    *,
    platform_id: str,
    white: str,
    black: str,
    time_class: str = "blitz",
    rated: bool = True,
    dias_atras: int = 0,
) -> Game:
    jugador = (
        await session.execute(select(Player).where(Player.username == white))
    ).scalar_one_or_none()
    if jugador is None:
        jugador = Player(platform="chesscom", username=white)
        session.add(jugador)
        await session.flush()
    partida = Game(
        player_id=jugador.id,
        platform="chesscom",
        platform_id=platform_id,
        pgn=PGN,
        white_username=white,
        white_rating=1500,
        white_result="win",
        black_username=black,
        black_rating=1480,
        black_result="checkmated",
        time_control="180",
        time_class=time_class,
        rules="chess",
        rated=rated,
        played_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=dias_atras),
        year=2024,
        month=1,
    )
    session.add(partida)
    await session.commit()
    return partida


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_list_games_ordena_por_mas_reciente_primero(db_session: AsyncSession) -> None:
    await _crear_partida(db_session, platform_id="g1", white="ana", black="beto", dias_atras=5)
    await _crear_partida(db_session, platform_id="g2", white="ana", black="beto", dias_atras=1)

    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.get("/games")
        assert respuesta.status_code == 200
        partidas = respuesta.json()
        assert len(partidas) == 2
        assert partidas[0]["white_rating"] == 1500
        # la más reciente (dias_atras=1) va primero
        fechas = [p["played_at"] for p in partidas]
        assert fechas == sorted(fechas, reverse=True)
    finally:
        app.dependency_overrides.clear()


async def test_list_games_filtra_por_username_y_color(db_session: AsyncSession) -> None:
    await _crear_partida(db_session, platform_id="g1", white="ana", black="beto")
    await _crear_partida(db_session, platform_id="g2", white="beto", black="ana")
    await _crear_partida(db_session, platform_id="g3", white="carla", black="dario")

    _override(db_session)
    try:
        with TestClient(app) as http:
            todas_de_ana = http.get("/games", params={"username": "ana"}).json()
            solo_blancas = http.get("/games", params={"username": "ana", "color": "white"}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(todas_de_ana) == 2
    assert len(solo_blancas) == 1
    assert solo_blancas[0]["white_username"] == "ana"


async def test_list_games_encuentra_al_jugador_sin_importar_mayusculas(
    db_session: AsyncSession,
) -> None:
    await _crear_partida(db_session, platform_id="g1", white="SirJsus", black="Rival")

    _override(db_session)
    try:
        with TestClient(app) as http:
            en_minusculas = http.get("/games", params={"username": "sirjsus"}).json()
            con_color = http.get("/games", params={"username": "sirjsus", "color": "white"}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(en_minusculas) == 1
    assert len(con_color) == 1


async def test_list_games_filtra_por_time_class_y_rated(db_session: AsyncSession) -> None:
    await _crear_partida(
        db_session, platform_id="g1", white="ana", black="beto", time_class="bullet"
    )
    await _crear_partida(
        db_session, platform_id="g2", white="ana", black="beto", time_class="blitz"
    )
    await _crear_partida(
        db_session, platform_id="g3", white="ana", black="beto", time_class="blitz", rated=False
    )

    _override(db_session)
    try:
        with TestClient(app) as http:
            blitz = http.get("/games", params={"time_class": "blitz"}).json()
            blitz_rated = http.get("/games", params={"time_class": "blitz", "rated": True}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(blitz) == 2
    assert len(blitz_rated) == 1


async def test_list_games_pagina_con_limit_y_offset(db_session: AsyncSession) -> None:
    for i in range(5):
        await _crear_partida(
            db_session, platform_id=f"g{i}", white="ana", black="beto", dias_atras=i
        )

    _override(db_session)
    try:
        with TestClient(app) as http:
            pagina1 = http.get("/games", params={"limit": 2, "offset": 0}).json()
            pagina2 = http.get("/games", params={"limit": 2, "offset": 2}).json()
    finally:
        app.dependency_overrides.clear()

    assert len(pagina1) == 2
    assert len(pagina2) == 2
    assert {p["played_at"] for p in pagina1}.isdisjoint({p["played_at"] for p in pagina2})


async def test_get_game_incluye_pgn(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session, platform_id="g1", white="ana", black="beto")

    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.get(f"/games/{partida.id}")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    assert respuesta.json()["pgn"] == PGN


async def test_get_game_inexistente_da_404(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            respuesta = http.get("/games/999999")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 404

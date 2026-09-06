"""Tests de estadísticas (RF-3). Lo delicado aquí es que el resultado de una
partida depende del color con el que jugó el usuario: la misma fila de `games`
es una victoria para uno y una derrota para el otro."""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.main import app
from lucia_api.services.stats import get_player_stats
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "a"]\n[Black "b"]\n[Result "1-0"]\n\n1. e4 e5 1-0\n'


async def _add_game(
    session: AsyncSession,
    *,
    platform_id: str,
    white: str,
    black: str,
    white_result: str,
    black_result: str,
    time_class: str = "blitz",
    white_rating: int = 1500,
    black_rating: int = 1500,
    eco: str | None = None,
    year: int = 2024,
    month: int = 1,
    dias_atras: int = 0,
) -> Game:
    jugador = Player(platform="chesscom", username=f"dummy-{platform_id}")
    session.add(jugador)
    await session.flush()
    partida = Game(
        player_id=jugador.id,
        platform="chesscom",
        platform_id=platform_id,
        pgn=PGN,
        white_username=white,
        white_rating=white_rating,
        white_result=white_result,
        black_username=black,
        black_rating=black_rating,
        black_result=black_result,
        time_control="180",
        time_class=time_class,
        rules="chess",
        rated=True,
        eco=eco,
        played_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=dias_atras),
        year=year,
        month=month,
    )
    session.add(partida)
    await session.commit()
    return partida


async def test_resultado_depende_del_color_del_jugador(db_session: AsyncSession) -> None:
    # Una sola partida: victoria de las blancas (ana) sobre beto.
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="checkmated",
    )

    de_ana = await get_player_stats(db_session, "ana")
    de_beto = await get_player_stats(db_session, "beto")

    assert (de_ana.overall.wins, de_ana.overall.losses) == (1, 0)
    assert (de_beto.overall.wins, de_beto.overall.losses) == (0, 1)


async def test_encuentra_al_jugador_sin_importar_mayusculas(db_session: AsyncSession) -> None:
    """chess.com da el perfil en minúsculas ("sirjsus") pero dentro del PGN el
    nombre va como lo escribió el jugador ("SirJsus"). Buscar por el nombre del
    perfil tiene que encontrar sus partidas igualmente."""
    await _add_game(
        db_session,
        platform_id="g1",
        white="SirJsus",
        black="Rival",
        white_result="win",
        black_result="resigned",
    )

    stats = await get_player_stats(db_session, "sirjsus")

    assert stats.total_games == 1
    assert stats.overall.wins == 1


async def test_cuenta_tablas_por_separado(db_session: AsyncSession) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="agreed",
        black_result="agreed",
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="ana",
        black="beto",
        white_result="stalemate",
        black_result="stalemate",
    )

    stats = await get_player_stats(db_session, "ana")

    assert stats.overall.draws == 2
    assert stats.overall.wins == 0
    assert stats.overall.score_percent == 50.0


async def test_agrupa_por_control_de_tiempo_con_el_rating_mas_reciente(
    db_session: AsyncSession,
) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
        time_class="bullet",
        white_rating=1400,
        dias_atras=10,
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
        time_class="bullet",
        white_rating=1450,
        dias_atras=1,  # más reciente: este rating es el que debe reportarse
    )
    await _add_game(
        db_session,
        platform_id="g3",
        white="beto",
        black="ana",
        white_result="win",
        black_result="resigned",
        time_class="rapid",
        black_rating=1600,
    )

    stats = await get_player_stats(db_session, "ana")
    por_control = {item.time_class: item for item in stats.by_time_class}

    assert por_control["bullet"].record.wins == 2
    assert por_control["bullet"].current_rating == 1450
    assert por_control["rapid"].record.losses == 1
    assert por_control["rapid"].current_rating == 1600


async def test_agrupa_partidas_por_mes(db_session: AsyncSession) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="b",
        white_result="win",
        black_result="resigned",
        year=2024,
        month=1,
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="ana",
        black="b",
        white_result="win",
        black_result="resigned",
        year=2024,
        month=2,
    )
    await _add_game(
        db_session,
        platform_id="g3",
        white="ana",
        black="b",
        white_result="win",
        black_result="resigned",
        year=2024,
        month=2,
    )

    stats = await get_player_stats(db_session, "ana")

    assert [(m.year, m.month, m.games) for m in stats.by_month] == [
        (2024, 1, 1),
        (2024, 2, 2),
    ]


async def test_rendimiento_por_apertura_separa_colores(db_session: AsyncSession) -> None:
    italiana = "https://www.chess.com/openings/Italian-Game"
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
        eco=italiana,
    )
    await _add_game(
        db_session,
        platform_id="g2",
        white="beto",
        black="ana",
        white_result="win",
        black_result="resigned",
        eco=italiana,
    )

    stats = await get_player_stats(db_session, "ana")
    por_color = {item.color: item for item in stats.by_opening}

    assert por_color["white"].opening == "Italian Game"  # nombre legible, no la URL
    assert por_color["white"].record.wins == 1
    assert por_color["black"].record.losses == 1


async def test_estadisticas_por_fase_solo_cuentan_jugadas_propias(
    db_session: AsyncSession,
) -> None:
    partida = await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
    )
    analisis = Analysis(
        game_id=partida.id,
        engine="stockfish",
        depth=10,
        multipv=1,
        status="done",
        white_accuracy=90.0,
        black_accuracy=70.0,
    )
    db_session.add(analisis)
    await db_session.flush()

    # Una jugada de cada color en apertura; la de las negras es un blunder.
    db_session.add_all(
        [
            AnalyzedMove(
                analysis_id=analisis.id,
                ply=0,
                color="white",
                san="e4",
                uci="e2e4",
                fen_before="x",
                classification="best",
                phase="opening",
                move_accuracy=99.0,
                win_percent_before=52.0,
                win_percent_after=52.0,
            ),
            AnalyzedMove(
                analysis_id=analisis.id,
                ply=1,
                color="black",
                san="g5",
                uci="g7g5",
                fen_before="x",
                classification="blunder",
                phase="opening",
                move_accuracy=10.0,
                win_percent_before=48.0,
                win_percent_after=8.0,
            ),
        ]
    )
    await db_session.commit()

    de_ana = await get_player_stats(db_session, "ana")
    de_beto = await get_player_stats(db_session, "beto")

    apertura_ana = next(p for p in de_ana.by_phase if p.phase == "opening")
    apertura_beto = next(p for p in de_beto.by_phase if p.phase == "opening")

    assert apertura_ana.moves == 1
    assert apertura_ana.blunders == 0
    assert apertura_ana.average_accuracy == 99.0

    assert apertura_beto.moves == 1
    assert apertura_beto.blunders == 1
    assert apertura_beto.average_win_percent_lost == 40.0

    # La precisión global también sale del bando correcto.
    assert de_ana.average_accuracy == 90.0
    assert de_beto.average_accuracy == 70.0
    assert de_ana.analyzed_games == 1


async def test_endpoint_stats_devuelve_el_resumen(db_session: AsyncSession) -> None:
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
    )

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.get("/stats", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    body = respuesta.json()
    assert body["username"] == "ana"
    assert body["overall"]["wins"] == 1
    assert body["overall"]["total"] == 1


async def test_endpoint_stats_sin_username_ni_configuracion_da_422(
    db_session: AsyncSession, monkeypatch
) -> None:
    monkeypatch.setattr("lucia_api.routers.stats.settings.chesscom_username", "")

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.get("/stats")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 422

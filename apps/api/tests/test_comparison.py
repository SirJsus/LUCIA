"""Comparación entre motores (RF-2.6). Lo que importa aquí es localizar las
jugadas donde Stockfish y Lc0 no opinan lo mismo, que es donde hay algo que
entender."""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.main import app
from lucia_api.services.comparison import ComparisonError, compare_analyses
from sqlalchemy.ext.asyncio import AsyncSession

PGN = '[White "a"]\n[Black "b"]\n[Result "1-0"]\n\n1. e4 e5 1-0\n'


async def _crear_partida(session: AsyncSession) -> Game:
    jugador = Player(platform="chesscom", username="ana")
    session.add(jugador)
    await session.flush()
    partida = Game(
        player_id=jugador.id,
        platform="chesscom",
        platform_id="g1",
        pgn=PGN,
        white_username="ana",
        white_rating=1500,
        white_result="win",
        black_username="beto",
        black_rating=1500,
        black_result="resigned",
        time_control="180",
        time_class="blitz",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2024,
        month=1,
    )
    session.add(partida)
    await session.flush()
    return partida


async def _crear_analisis(
    session: AsyncSession,
    game_id: int,
    engine: str,
    jugadas: list[tuple[int, str, float, str | None, str]],
    status: str = "done",
) -> Analysis:
    """`jugadas` = (ply, san, win_percent_after, best_move_uci, classification)."""
    analisis = Analysis(game_id=game_id, engine=engine, depth=10, multipv=1, status=status)
    session.add(analisis)
    await session.flush()
    for ply, san, win_after, best, clasificacion in jugadas:
        session.add(
            AnalyzedMove(
                analysis_id=analisis.id,
                ply=ply,
                color="white" if ply % 2 == 0 else "black",
                san=san,
                uci="e2e4",
                fen_before="x",
                classification=clasificacion,
                phase="opening",
                move_accuracy=90.0,
                win_percent_before=50.0,
                win_percent_after=win_after,
                best_move_uci=best,
            )
        )
    await session.commit()
    return analisis


async def test_detecta_donde_los_motores_discrepan(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session)
    # Ply 0: coinciden. Ply 1: Lc0 valora la posición 30 puntos peor.
    sf = await _crear_analisis(
        db_session,
        partida.id,
        "stockfish",
        [(0, "e4", 52.0, "e2e4", "best"), (1, "e5", 48.0, "e7e5", "best")],
    )
    lc0 = await _crear_analisis(
        db_session,
        partida.id,
        "lc0",
        [(0, "e4", 51.0, "e2e4", "best"), (1, "e5", 18.0, "c7c5", "inaccuracy")],
    )

    comparacion = await compare_analyses(db_session, sf.id, lc0.id)

    assert comparacion.total_moves == 2
    assert comparacion.agreed_best_moves == 1  # solo coinciden en el ply 0
    assert comparacion.best_move_agreement_percent == 50.0
    assert len(comparacion.disagreements) == 1

    discrepancia = comparacion.disagreements[0]
    assert discrepancia.ply == 1
    assert discrepancia.win_percent_gap == 30.0
    assert discrepancia.same_best_move is False
    assert discrepancia.classification_a == "best"
    assert discrepancia.classification_b == "inaccuracy"


async def test_las_diferencias_pequenas_no_cuentan_como_discrepancia(
    db_session: AsyncSession,
) -> None:
    """Dos motores nunca dan el mismo número exacto; sin umbral, todas las
    jugadas saldrían como discrepancia."""
    partida = await _crear_partida(db_session)
    sf = await _crear_analisis(
        db_session, partida.id, "stockfish", [(0, "e4", 52.0, "e2e4", "best")]
    )
    lc0 = await _crear_analisis(db_session, partida.id, "lc0", [(0, "e4", 55.0, "e2e4", "best")])

    comparacion = await compare_analyses(db_session, sf.id, lc0.id)

    assert comparacion.disagreements == []
    assert comparacion.agreed_best_moves == 1


async def test_el_umbral_es_ajustable(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session)
    sf = await _crear_analisis(
        db_session, partida.id, "stockfish", [(0, "e4", 52.0, "e2e4", "best")]
    )
    lc0 = await _crear_analisis(db_session, partida.id, "lc0", [(0, "e4", 55.0, "e2e4", "best")])

    estricta = await compare_analyses(db_session, sf.id, lc0.id, threshold=1.0)

    assert len(estricta.disagreements) == 1


async def test_las_discrepancias_van_de_mayor_a_menor(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session)
    sf = await _crear_analisis(
        db_session,
        partida.id,
        "stockfish",
        [(0, "e4", 50.0, "e2e4", "best"), (1, "e5", 50.0, "e7e5", "best")],
    )
    lc0 = await _crear_analisis(
        db_session,
        partida.id,
        "lc0",
        [(0, "e4", 65.0, "d2d4", "good"), (1, "e5", 10.0, "c7c5", "blunder")],
    )

    comparacion = await compare_analyses(db_session, sf.id, lc0.id)

    assert [d.win_percent_gap for d in comparacion.disagreements] == [40.0, 15.0]


async def test_solo_compara_los_plies_presentes_en_ambos(db_session: AsyncSession) -> None:
    """Si un análisis se cortó a medias, la parte que falta no se compara."""
    partida = await _crear_partida(db_session)
    sf = await _crear_analisis(
        db_session,
        partida.id,
        "stockfish",
        [(0, "e4", 50.0, "e2e4", "best"), (1, "e5", 50.0, "e7e5", "best")],
    )
    lc0 = await _crear_analisis(db_session, partida.id, "lc0", [(0, "e4", 50.0, "e2e4", "best")])

    comparacion = await compare_analyses(db_session, sf.id, lc0.id)

    assert comparacion.total_moves == 1


async def test_rechaza_comparar_analisis_de_partidas_distintas(
    db_session: AsyncSession,
) -> None:
    partida1 = await _crear_partida(db_session)
    jugador2 = Player(platform="chesscom", username="otro")
    db_session.add(jugador2)
    await db_session.flush()
    partida2 = Game(
        player_id=jugador2.id,
        platform="chesscom",
        platform_id="g2",
        pgn=PGN,
        white_username="x",
        white_rating=1,
        white_result="win",
        black_username="y",
        black_rating=1,
        black_result="resigned",
        time_control="180",
        time_class="blitz",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2024,
        month=1,
    )
    db_session.add(partida2)
    await db_session.flush()

    a = await _crear_analisis(db_session, partida1.id, "stockfish", [])
    b = await _crear_analisis(db_session, partida2.id, "lc0", [])

    with pytest.raises(ComparisonError, match="partidas distintas"):
        await compare_analyses(db_session, a.id, b.id)


async def test_rechaza_comparar_si_alguno_no_ha_terminado(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session)
    a = await _crear_analisis(db_session, partida.id, "stockfish", [])
    b = await _crear_analisis(db_session, partida.id, "lc0", [], status="running")

    with pytest.raises(ComparisonError, match="terminados"):
        await compare_analyses(db_session, a.id, b.id)


async def test_endpoint_de_comparacion(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session)
    sf = await _crear_analisis(
        db_session, partida.id, "stockfish", [(0, "e4", 52.0, "e2e4", "best")]
    )
    lc0 = await _crear_analisis(db_session, partida.id, "lc0", [(0, "e4", 20.0, "d2d4", "mistake")])

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.get(
                "/analysis/compare", params={"analysis_a": sf.id, "analysis_b": lc0.id}
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200, respuesta.text
    body = respuesta.json()
    assert body["engine_a"] == "stockfish"
    assert body["engine_b"] == "lc0"
    assert len(body["disagreements"]) == 1
    assert body["disagreements"][0]["win_percent_gap"] == 32.0


async def test_compare_no_se_confunde_con_un_id_de_analisis(
    db_session: AsyncSession,
) -> None:
    """`/analysis/compare` se declara antes que `/analysis/{analysis_id}`."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            respuesta = http.get("/analysis/compare", params={"analysis_a": 999, "analysis_b": 998})
    finally:
        app.dependency_overrides.clear()

    # 422 del servicio (no existen), no un error de tipo de ruta.
    assert respuesta.status_code == 422
    assert "no existe" in respuesta.json()["detail"]

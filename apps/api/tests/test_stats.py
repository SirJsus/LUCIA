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
    opening_name: str | None = None,
    opening_eco: str | None = None,
    year: int = 2024,
    month: int = 1,
    days_ago: int = 0,
) -> Game:
    player = Player(platform="chesscom", username=f"dummy-{platform_id}")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
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
        opening_name=opening_name,
        opening_eco=opening_eco,
        played_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=days_ago),
        year=year,
        month=month,
    )
    session.add(game)
    await session.commit()
    return game


async def test_outcome_depends_on_the_player_color(db_session: AsyncSession) -> None:
    # Una sola partida: victoria de las blancas (ana) sobre beto.
    await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="checkmated",
    )

    ana_stats = await get_player_stats(db_session, "ana")
    beto_stats = await get_player_stats(db_session, "beto")

    assert (ana_stats.overall.wins, ana_stats.overall.losses) == (1, 0)
    assert (beto_stats.overall.wins, beto_stats.overall.losses) == (0, 1)


async def test_finds_the_player_regardless_of_case(db_session: AsyncSession) -> None:
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


async def test_counts_draws_separately(db_session: AsyncSession) -> None:
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


async def test_groups_by_time_class_with_the_most_recent_rating(
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
        days_ago=10,
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
        days_ago=1,  # más reciente: este rating es el que debe reportarse
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
    by_time_class = {item.time_class: item for item in stats.by_time_class}

    assert by_time_class["bullet"].record.wins == 2
    assert by_time_class["bullet"].current_rating == 1450
    assert by_time_class["rapid"].record.losses == 1
    assert by_time_class["rapid"].current_rating == 1600


async def test_groups_games_by_month(db_session: AsyncSession) -> None:
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


async def test_opening_performance_separates_colors(db_session: AsyncSession) -> None:
    for platform_id, white, black in (("g1", "ana", "beto"), ("g2", "beto", "ana")):
        await _add_game(
            db_session,
            platform_id=platform_id,
            white=white,
            black=black,
            white_result="win",
            black_result="resigned",
            opening_name="Italian Game",
            opening_eco="C50",
        )

    stats = await get_player_stats(db_session, "ana")
    by_color = {item.color: item for item in stats.by_opening}

    assert by_color["white"].opening == "Italian Game"
    assert by_color["white"].eco == "C50"  # la tabla propia sí trae el código
    assert by_color["white"].record.wins == 1
    assert by_color["black"].record.losses == 1


async def test_phase_stats_only_count_own_moves(
    db_session: AsyncSession,
) -> None:
    game = await _add_game(
        db_session,
        platform_id="g1",
        white="ana",
        black="beto",
        white_result="win",
        black_result="resigned",
    )
    analysis = Analysis(
        game_id=game.id,
        engine="stockfish",
        depth=10,
        multipv=1,
        status="done",
        white_accuracy=90.0,
        black_accuracy=70.0,
    )
    db_session.add(analysis)
    await db_session.flush()

    # Una jugada de cada color en apertura; la de las negras es un blunder.
    db_session.add_all(
        [
            AnalyzedMove(
                analysis_id=analysis.id,
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
                analysis_id=analysis.id,
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

    ana_stats = await get_player_stats(db_session, "ana")
    beto_stats = await get_player_stats(db_session, "beto")

    ana_opening_phase = next(p for p in ana_stats.by_phase if p.phase == "opening")
    beto_opening_phase = next(p for p in beto_stats.by_phase if p.phase == "opening")

    assert ana_opening_phase.moves == 1
    assert ana_opening_phase.blunders == 0
    assert ana_opening_phase.average_accuracy == 99.0

    assert beto_opening_phase.moves == 1
    assert beto_opening_phase.blunders == 1
    assert beto_opening_phase.average_win_percent_lost == 40.0

    # La precisión global también sale del bando correcto.
    assert ana_stats.average_accuracy == 90.0
    assert beto_stats.average_accuracy == 70.0
    assert ana_stats.analyzed_games == 1


async def test_stats_endpoint_returns_the_summary(db_session: AsyncSession) -> None:
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
            response = http.get("/stats", params={"username": "ana"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "ana"
    assert body["overall"]["wins"] == 1
    assert body["overall"]["total"] == 1


async def test_stats_endpoint_without_username_or_config_returns_422(
    db_session: AsyncSession, monkeypatch
) -> None:
    monkeypatch.setattr("lucia_api.dependencies.settings.chesscom_username", "")

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    try:
        with TestClient(app) as http:
            response = http.get("/stats")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def _add_analyzed_game(
    session: AsyncSession,
    *,
    platform_id: str,
    white: str,
    black: str,
    moves: list[dict],
    clocks: list[float] | None = None,
    opening_name: str | None = None,
    opening_eco: str | None = None,
    year: int = 2024,
    month: int = 1,
    white_rating: int = 1500,
) -> Game:
    """Una partida con análisis terminado y las jugadas que se le pasen.

    Cada dict de `moves` son los campos de `AnalyzedMove` que el test necesita;
    el resto se rellena con valores neutros para no repetirlos en cada caso.
    """
    game = await _add_game(
        session,
        platform_id=platform_id,
        white=white,
        black=black,
        white_result="win",
        black_result="checkmated",
        opening_name=opening_name,
        opening_eco=opening_eco,
        year=year,
        month=month,
        white_rating=white_rating,
    )
    game.clocks_json = clocks
    analysis = Analysis(game_id=game.id, engine="stockfish", depth=10, multipv=3, status="done")
    session.add(analysis)
    await session.flush()
    for ply, move in enumerate(moves):
        session.add(
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=move.get("ply", ply),
                color=move.get("color", "white"),
                san=move.get("san", "e4"),
                uci="e2e4",
                fen_before=move.get("fen_before", "x"),
                classification=move.get("classification", "good"),
                phase=move.get("phase", "middlegame"),
                move_accuracy=move.get("move_accuracy", 90.0),
                win_percent_before=move.get("win_percent_before", 50.0),
                win_percent_after=move.get("win_percent_after", 50.0),
                alternatives_json=move.get("alternatives_json"),
            )
        )
    await session.commit()
    return game


async def test_mistakes_are_grouped_by_type(db_session: AsyncSession) -> None:
    """RF-3.4: no basta con cuántos errores hay, hace falta saber por qué."""
    await _add_analyzed_game(
        db_session,
        platform_id="patrones-1",
        white="ana",
        black="beto",
        # Reloj por media jugada: la tercera jugada de ana se juega con 5 s.
        clocks=[120.0, 120.0, 90.0, 90.0, 5.0, 60.0],
        moves=[
            {"ply": 0, "color": "white", "classification": "good"},
            {"ply": 1, "color": "black", "classification": "blunder"},
            {"ply": 2, "color": "white", "classification": "mistake", "phase": "endgame"},
            {"ply": 3, "color": "black", "classification": "good"},
            {"ply": 4, "color": "white", "classification": "blunder"},
            {"ply": 5, "color": "black", "classification": "good"},
        ],
    )

    stats = await get_player_stats(db_session, "ana")

    by_type = {item.mistake_type: item for item in stats.by_mistake_type}
    # El de la jugada 4 se juega con 5 segundos: la causa es el reloj.
    assert by_type["time"].mistakes == 1
    assert by_type["time"].blunders == 1
    # El de la jugada 2 es un final sin captura ni jaque que ver.
    assert by_type["endgame"].mistakes == 1
    # Y el blunder del rival no cuenta: son los patrones de ana, no los de beto.
    assert sum(item.mistakes for item in stats.by_mistake_type) == 2


async def test_time_pressure_groups_moves_by_clock_left(db_session: AsyncSession) -> None:
    """RF-3.5: cómo cae la calidad de juego según baja el reloj."""
    await _add_analyzed_game(
        db_session,
        platform_id="patrones-2",
        white="ana",
        black="beto",
        clocks=[120.0, 120.0, 8.0, 60.0],
        moves=[
            {"ply": 0, "color": "white", "move_accuracy": 95.0},
            {"ply": 1, "color": "black"},
            {"ply": 2, "color": "white", "move_accuracy": 25.0, "classification": "blunder"},
            {"ply": 3, "color": "black"},
        ],
    )

    stats = await get_player_stats(db_session, "ana")

    buckets = {bucket.max_seconds_left: bucket for bucket in stats.by_time_left}
    assert buckets[None].moves == 1  # con 120 s: tiempo de sobra
    assert buckets[None].average_accuracy == 95.0
    assert buckets[10.0].moves == 1  # con 8 s: apuros
    assert buckets[10.0].blunders == 1
    assert stats.time_trouble is not None
    assert stats.time_trouble.games_in_time_trouble == 1
    assert stats.time_trouble.analyzed_games_with_clocks == 1


async def test_opening_exit_evaluation_per_opening(db_session: AsyncSession) -> None:
    """RF-3.2: con qué posición se sale de la apertura."""
    await _add_analyzed_game(
        db_session,
        platform_id="patrones-3",
        white="ana",
        black="beto",
        opening_name="Italian Game",
        opening_eco="C50",
        moves=[
            {"ply": 0, "color": "white", "phase": "opening", "win_percent_after": 55.0},
            {"ply": 2, "color": "white", "phase": "opening", "win_percent_after": 61.0},
            {"ply": 4, "color": "white", "phase": "middlegame", "win_percent_after": 40.0},
        ],
    )

    stats = await get_player_stats(db_session, "ana")

    italian = next(item for item in stats.by_opening if item.opening == "Italian Game")
    # La última jugada en apertura es la del ply 2, no la mejor ni la media.
    assert italian.average_opening_exit_win_percent == 61.0


async def test_a_game_analyzed_twice_counts_once(db_session: AsyncSession) -> None:
    """Una partida con análisis de los dos motores (RF-2.6) no puede contar
    doble: diría que se juega el doble de partidas y de errores."""
    game = await _add_analyzed_game(
        db_session,
        platform_id="patrones-4",
        white="ana",
        black="beto",
        moves=[{"ply": 0, "color": "white", "classification": "blunder"}],
    )
    second_analysis = Analysis(game_id=game.id, engine="lc0", depth=1600, multipv=1, status="done")
    db_session.add(second_analysis)
    await db_session.flush()
    db_session.add(
        AnalyzedMove(
            analysis_id=second_analysis.id,
            ply=0,
            color="white",
            san="e4",
            uci="e2e4",
            fen_before="x",
            classification="blunder",
            phase="middlegame",
            move_accuracy=20.0,
            win_percent_before=50.0,
            win_percent_after=20.0,
        )
    )
    await db_session.commit()

    stats = await get_player_stats(db_session, "ana")

    assert stats.analyzed_games == 1
    assert sum(item.mistakes for item in stats.by_mistake_type) == 1


async def test_trends_report_each_month_per_hundred_moves(db_session: AsyncSession) -> None:
    """RF-3.7: la evolución se lee por mes y normalizada.

    Dos meses con distinto número de partidas: en recuento crudo el segundo
    parecería mucho peor solo por haber jugado más, y por cada cien jugadas se
    ve que en realidad se falla igual.
    """
    await _add_analyzed_game(
        db_session,
        platform_id="tendencia-1",
        white="ana",
        black="beto",
        year=2024,
        month=1,
        white_rating=1500,
        moves=[
            {"ply": 0, "color": "white", "classification": "mistake", "move_accuracy": 40.0},
            {"ply": 2, "color": "white", "move_accuracy": 100.0},
        ],
    )
    for index in (2, 3):
        await _add_analyzed_game(
            db_session,
            platform_id=f"tendencia-{index}",
            white="ana",
            black="beto",
            year=2024,
            month=2,
            white_rating=1500 + index,
            moves=[
                {"ply": 0, "color": "white", "classification": "mistake", "move_accuracy": 40.0},
                {"ply": 2, "color": "white", "move_accuracy": 100.0},
            ],
        )

    stats = await get_player_stats(db_session, "ana")

    january, february = stats.trends.by_month
    assert (january.year, january.month, january.analyzed_games) == (2024, 1, 1)
    assert (february.year, february.month, february.analyzed_games) == (2024, 2, 2)
    # Dos jugadas en enero y cuatro en febrero, pero la misma tasa de error.
    assert january.quality.total_mistakes_per_hundred_moves == 50.0
    assert february.quality.total_mistakes_per_hundred_moves == 50.0
    assert january.quality.average_accuracy == 70.0
    # El rating es el de la última partida del mes en el control más jugado.
    assert stats.trends.rating_time_class == "blitz"
    assert (january.rating, february.rating) == (1500, 1503)


async def test_trends_leave_out_months_without_analysis(db_session: AsyncSession) -> None:
    """Un mes jugado pero sin analizar no es un mes con precisión cero: no
    aparece en la tendencia, aunque sí en "partidas por mes" (RF-3.1)."""
    await _add_game(
        db_session,
        platform_id="sin-analizar",
        white="ana",
        black="beto",
        white_result="win",
        black_result="checkmated",
        year=2024,
        month=3,
    )
    await _add_analyzed_game(
        db_session,
        platform_id="analizada",
        white="ana",
        black="beto",
        year=2024,
        month=4,
        moves=[{"ply": 0, "color": "white"}],
    )

    stats = await get_player_stats(db_session, "ana")

    assert len(stats.by_month) == 2
    assert [(item.year, item.month) for item in stats.trends.by_month] == [(2024, 4)]
    # Un solo mes no se puede comparar con nada.
    assert stats.trends.change is None

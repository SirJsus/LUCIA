"""Exportación a PGN anotado (RF-5.5): el servicio y el endpoint."""

from __future__ import annotations

import datetime as dt
import io
from collections.abc import AsyncIterator

import chess
import chess.pgn
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.main import app
from lucia_api.services.pgn_export import export_annotated_pgn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# El mate del loco: 1.f3 e5 2.g4 Qh4#. Cuatro jugadas, dos de ellas malas, y
# la posición inicial es conocida, así que las líneas del motor se pueden
# escribir a mano sin que dejen de ser legales.
PGN = '[White "a"]\n[Black "b"]\n[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'

#: Una línea del motor tal como se guarda (ver `services.analysis._serialize_line`).
BEST_LINE_FROM_START = [{"score_cp": 30, "score_mate": None, "pv": ["e2e4", "e7e5", "g1f3"]}]


async def _create_analysis(session: AsyncSession, *, status: str = "done") -> Analysis:
    """Una partida con su análisis de cuatro jugadas, clasificadas a mano."""
    player = Player(platform="chesscom", username="a")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id="partida-export-1",
        pgn=PGN,
        white_username="Durán, Jesús",
        white_rating=1000,
        white_result="checkmated",
        black_username="b",
        black_rating=1000,
        black_result="win",
        time_control="600",
        time_class="rapid",
        rules="chess",
        rated=True,
        played_at=dt.datetime(2026, 3, 14, tzinfo=dt.UTC),
        year=2026,
        month=3,
    )
    session.add(game)
    await session.flush()

    analysis = Analysis(
        game_id=game.id,
        engine="stockfish",
        depth=12,
        multipv=2,
        status=status,
        white_accuracy=31.25,
        black_accuracy=99.5,
    )
    session.add(analysis)
    await session.flush()

    board = chess.Board()
    parsed = chess.pgn.read_game(io.StringIO(PGN))
    assert parsed is not None
    played_moves = list(parsed.mainline_moves())
    # Solo la primera jugada lleva alternativas guardadas: así el mismo test
    # cubre la jugada con variante y las que se quedan sin ella.
    classifications = ["mistake", "best", "blunder", "best"]
    for ply, (move, classification) in enumerate(zip(played_moves, classifications, strict=True)):
        session.add(
            AnalyzedMove(
                analysis_id=analysis.id,
                ply=ply,
                color="white" if ply % 2 == 0 else "black",
                san=board.san(move),
                uci=move.uci(),
                fen_before=board.fen(),
                classification=classification,
                phase="opening",
                move_accuracy=50.0,
                win_percent_before=50.0,
                win_percent_after=40.0,
                best_move_uci="e2e4" if ply == 0 else move.uci(),
                alternatives_json=BEST_LINE_FROM_START if ply == 0 else None,
            )
        )
        board.push(move)

    await session.commit()
    return analysis


async def _analysis_to_export(
    db_session: AsyncSession,
) -> tuple[Game, Analysis, list[AnalyzedMove]]:
    """La partida, su análisis y sus jugadas: lo que `export_annotated_pgn`
    recibe del router."""
    analysis = await _create_analysis(db_session)
    game = await db_session.get(Game, analysis.game_id)
    assert game is not None
    moves = await db_session.execute(select(AnalyzedMove).order_by(AnalyzedMove.ply))
    return game, analysis, list(moves.scalars())


def _exported(pgn_text: str) -> chess.pgn.Game:
    """El PGN exportado, releído: si no vuelve a parsear, no sirve de nada."""
    parsed = chess.pgn.read_game(io.StringIO(pgn_text))
    assert parsed is not None
    return parsed


async def test_the_exported_pgn_keeps_the_game(db_session: AsyncSession) -> None:
    game, analysis, moves = await _analysis_to_export(db_session)

    parsed = _exported(export_annotated_pgn(game, analysis, moves, {}))

    assert [move.uci() for move in parsed.mainline_moves()] == ["f2f3", "e7e5", "g2g4", "d8h4"]
    assert parsed.headers["Result"] == "0-1"
    # Las cabeceras son las del PGN original, no las columnas de `games`: la
    # fila dice "Durán, Jesús" porque la importación resolvió ese bando al
    # usuario de LUCIA (RF-1.5), y el archivo que se exporta tiene que seguir
    # diciendo lo que decía el de origen.
    assert parsed.headers["White"] == "a"


async def test_the_exported_pgn_says_who_annotated_it(db_session: AsyncSession) -> None:
    game, analysis, moves = await _analysis_to_export(db_session)

    parsed = _exported(export_annotated_pgn(game, analysis, moves, {}))

    assert parsed.headers["Annotator"] == "LUCIA · stockfish profundidad 12"
    assert parsed.headers["WhiteAccuracy"] == "31.2"
    assert parsed.headers["BlackAccuracy"] == "99.5"


async def test_every_move_is_commented_and_the_bad_ones_are_marked(
    db_session: AsyncSession,
) -> None:
    game, analysis, moves = await _analysis_to_export(db_session)

    parsed = _exported(export_annotated_pgn(game, analysis, moves, {}))
    nodes = list(parsed.mainline())

    assert all(node.comment for node in nodes)
    assert "Error" in nodes[0].comment
    assert nodes[0].nags == {chess.pgn.NAG_MISTAKE}
    assert nodes[2].nags == {chess.pgn.NAG_BLUNDER}
    # Una jugada que coincide con la del motor no lleva símbolo: no se premia
    # un acierto que el análisis no mide.
    assert nodes[1].nags == set()


async def test_the_comment_gives_the_win_percent_from_whites_point_of_view(
    db_session: AsyncSession,
) -> None:
    game, analysis, moves = await _analysis_to_export(db_session)

    nodes = list(_exported(export_annotated_pgn(game, analysis, moves, {})).mainline())

    # Todas las jugadas se guardaron con 40 % para quien las jugó: las blancas
    # salen con 40 % y las negras, giradas, con 60 %.
    assert "40 % prob. victoria blancas" in nodes[0].comment
    assert "60 % prob. victoria blancas" in nodes[1].comment


async def test_the_engine_line_goes_in_as_a_variation(db_session: AsyncSession) -> None:
    game, analysis, moves = await _analysis_to_export(db_session)

    parsed = _exported(export_annotated_pgn(game, analysis, moves, {}))
    first_move = parsed.variations[0]

    # La variante cuelga de la posición inicial, no de 1.f3: es otra forma de
    # seguir desde ahí.
    assert len(parsed.variations) == 2
    assert parsed.variations[1].move.uci() == "e2e4"
    assert "mejor 1.e4" in first_move.comment


async def test_a_move_without_saved_lines_is_commented_but_has_no_variation(
    db_session: AsyncSession,
) -> None:
    game, analysis, moves = await _analysis_to_export(db_session)

    nodes = list(_exported(export_annotated_pgn(game, analysis, moves, {})).mainline())

    # 2.g4 es un blunder sin alternativas guardadas ni caché que rescatar.
    assert "Blunder" in nodes[2].comment
    assert len(nodes[1].variations) == 1


def _override(db_session: AsyncSession):
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_get_analysis_pgn_downloads_a_file(db_session: AsyncSession) -> None:
    analysis = await _create_analysis(db_session)
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get(f"/analysis/{analysis.id}/pgn")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-chess-pgn")
    # El nombre viaja en una cabecera HTTP y acaba en el disco del usuario:
    # sin acentos, sin comas y sin espacios.
    assert response.headers["content-disposition"] == (
        'attachment; filename="lucia-duran-jesus-b-2026-03-14.pgn"'
    )
    assert "Annotator" in response.text


async def test_an_unfinished_analysis_is_not_exported(db_session: AsyncSession) -> None:
    analysis = await _create_analysis(db_session, status="running")
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get(f"/analysis/{analysis.id}/pgn")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


async def test_exporting_an_analysis_that_does_not_exist_is_a_404(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.get("/analysis/999/pgn")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

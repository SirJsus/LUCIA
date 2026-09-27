import datetime as dt

from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.services.analysis import run_analysis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .conftest import requires_stockfish

# Trampa del tonto: mate en 2, con un blunder evidente de las blancas (g2g4).
PGN = '[White "a"]\n[Black "b"]\n[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'

# Partida de ventaja (odds chess): las blancas empiezan sin dama ni torres, y
# el PGN lo dice con `[SetUp "1"]` + `[FEN ...]`.
ODDS_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NB1KBN1 w kq - 0 1"
ODDS_PGN = (
    '[White "a"]\n[Black "b"]\n[Result "0-1"]\n'
    f'[SetUp "1"]\n[FEN "{ODDS_STARTING_FEN}"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'
)


async def _create_game(session: AsyncSession, pgn: str = PGN) -> Game:
    player = Player(platform="chesscom", username="prueba")
    session.add(player)
    await session.flush()
    game = Game(
        player_id=player.id,
        platform="chesscom",
        platform_id="partida-1",
        pgn=pgn,
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
    await session.flush()
    return game


async def _load_analyzed_moves(session: AsyncSession, analysis: Analysis) -> list[AnalyzedMove]:
    """Las jugadas que dejó el análisis, en orden de ply."""
    query = select(AnalyzedMove).where(AnalyzedMove.analysis_id == analysis.id)
    return list(await session.scalars(query.order_by(AnalyzedMove.ply)))


@requires_stockfish
async def test_run_analysis_persists_moves_and_accuracy(db_session: AsyncSession) -> None:
    game = await _create_game(db_session)
    analysis = Analysis(game_id=game.id, engine="stockfish", depth=8, multipv=1)
    db_session.add(analysis)
    await db_session.flush()

    progress_events: list[tuple[int, int]] = []

    async def record_progress(ply: int, total: int) -> None:
        progress_events.append((ply, total))

    await run_analysis(db_session, analysis, game.pgn, on_progress=record_progress)

    assert analysis.status == "done"
    assert analysis.finished_at is not None
    assert analysis.white_accuracy is not None
    assert analysis.black_accuracy is not None
    assert analysis.white_accuracy < 90  # el blunder final tiene que notarse

    moves = await _load_analyzed_moves(db_session, analysis)
    assert len(moves) == 4  # f3, e5, g4, Qh4#
    assert moves[2].uci == "g2g4"
    assert moves[2].classification in {"mistake", "blunder"}

    # 5 posiciones evaluadas (inicial + 4 jugadas) => 5 llamadas de progreso.
    assert len(progress_events) == 5


@requires_stockfish
async def test_run_analysis_with_invalid_pgn_leaves_error_status(db_session: AsyncSession) -> None:
    # python-chess es permisivo con texto basura (lo lee como partida vacía, no
    # como error); un PGN vacío es el caso que sí da None.
    game = await _create_game(db_session, pgn="")
    analysis = Analysis(game_id=game.id, engine="stockfish", depth=8, multipv=1)
    db_session.add(analysis)
    await db_session.flush()

    await run_analysis(db_session, analysis, game.pgn)

    assert analysis.status == "error"
    assert analysis.error is not None


@requires_stockfish
async def test_run_analysis_uses_the_starting_position_of_the_pgn(
    db_session: AsyncSession,
) -> None:
    """Una partida con `[SetUp "1"]` + `[FEN ...]` se analiza desde su propia
    posición, no desde el tablero inicial de siempre."""
    game = await _create_game(db_session, pgn=ODDS_PGN)
    analysis = Analysis(game_id=game.id, engine="stockfish", depth=8, multipv=1)
    db_session.add(analysis)
    await db_session.flush()

    await run_analysis(db_session, analysis, game.pgn)

    assert analysis.status == "done"
    moves = await _load_analyzed_moves(db_session, analysis)
    assert moves[0].fen_before == ODDS_STARTING_FEN

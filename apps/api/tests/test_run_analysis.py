import datetime as dt

from lucia_api.db.models import Analysis, AnalyzedMove, Game, Player
from lucia_api.services.analysis import run_analysis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .conftest import requiere_stockfish

# Trampa del tonto: mate en 2, con un blunder evidente de las blancas (g2g4).
PGN = '[White "a"]\n[Black "b"]\n[Result "0-1"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n'


async def _crear_partida(session: AsyncSession) -> Game:
    jugador = Player(platform="chesscom", username="prueba")
    session.add(jugador)
    await session.flush()
    partida = Game(
        player_id=jugador.id,
        platform="chesscom",
        platform_id="partida-1",
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
    await session.flush()
    return partida


@requiere_stockfish
async def test_run_analysis_persiste_jugadas_y_precision(db_session: AsyncSession) -> None:
    partida = await _crear_partida(db_session)
    analisis = Analysis(game_id=partida.id, engine="stockfish", depth=8, multipv=1)
    db_session.add(analisis)
    await db_session.flush()

    eventos_progreso: list[tuple[int, int]] = []

    async def progreso(ply: int, total: int) -> None:
        eventos_progreso.append((ply, total))

    await run_analysis(db_session, analisis, partida, on_progress=progreso)

    assert analisis.status == "done"
    assert analisis.finished_at is not None
    assert analisis.white_accuracy is not None
    assert analisis.black_accuracy is not None
    assert analisis.white_accuracy < 90  # el blunder final tiene que notarse

    jugadas = (
        (
            await db_session.execute(
                select(AnalyzedMove)
                .where(AnalyzedMove.analysis_id == analisis.id)
                .order_by(AnalyzedMove.ply)
            )
        )
        .scalars()
        .all()
    )
    assert len(jugadas) == 4  # f3, e5, g4, Qh4#
    assert jugadas[2].uci == "g2g4"
    assert jugadas[2].classification in {"mistake", "blunder"}

    # 5 posiciones evaluadas (inicial + 4 jugadas) => 5 llamadas de progreso.
    assert len(eventos_progreso) == 5


@requiere_stockfish
async def test_run_analysis_pgn_invalido_deja_estado_error(db_session: AsyncSession) -> None:
    jugador = Player(platform="chesscom", username="prueba2")
    db_session.add(jugador)
    await db_session.flush()
    partida = Game(
        player_id=jugador.id,
        platform="chesscom",
        platform_id="partida-invalida",
        # python-chess es permisivo con texto basura (lo lee como partida
        # vacía, no como error); un PGN vacío es el caso que sí da None.
        pgn="",
        white_username="a",
        white_rating=1000,
        white_result="win",
        black_username="b",
        black_rating=1000,
        black_result="resigned",
        time_control="600",
        time_class="rapid",
        rules="chess",
        rated=True,
        played_at=dt.datetime.now(dt.UTC),
        year=2024,
        month=1,
    )
    db_session.add(partida)
    await db_session.flush()
    analisis = Analysis(game_id=partida.id, engine="stockfish", depth=8, multipv=1)
    db_session.add(analisis)
    await db_session.flush()

    await run_analysis(db_session, analisis, partida)

    assert analisis.status == "error"
    assert analisis.error is not None

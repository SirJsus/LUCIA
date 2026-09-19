import chess
import chess.engine
from lucia_api.db.models import PositionCache
from lucia_api.services.analysis import CachedEngineBridge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class FakeEngine:
    """Cuenta cuántas veces se le pregunta, para probar que la caché evita
    repetir la consulta al motor real."""

    def __init__(
        self,
        lines: list[chess.engine.InfoDict],
        limit_kind: str = "depth",
        weights: str | None = None,
    ) -> None:
        self.calls = 0
        self._lines = lines
        extra_options = {"WeightsFile": weights} if weights else {}
        self.config = type(
            "Config",
            (),
            {
                "limit_kind": limit_kind,
                "limit_value": 10,
                "multipv": 1,
                "extra_options": extra_options,
            },
        )()

    async def analyze(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        self.calls += 1
        return self._lines


def _line(
    cp: int = 40,
    mate: int | None = None,
    wdl: tuple[int, int, int] | None = None,
) -> chess.engine.InfoDict:
    score = chess.engine.Mate(mate) if mate is not None else chess.engine.Cp(cp)
    line: chess.engine.InfoDict = {
        "score": chess.engine.PovScore(score, chess.WHITE),
        "pv": [chess.Move.from_uci("e2e4")],
    }
    if wdl is not None:
        line["wdl"] = chess.engine.PovWdl(chess.engine.Wdl(*wdl), chess.WHITE)
    return line


async def test_second_query_of_the_same_position_does_not_call_the_engine(
    db_session: AsyncSession,
) -> None:
    fake_engine = FakeEngine([_line()])
    cached_engine = CachedEngineBridge(db_session, fake_engine, "stockfish")
    board = chess.Board()

    await cached_engine.analyze(board)
    await cached_engine.analyze(board)

    assert fake_engine.calls == 1

    total = (await db_session.execute(select(func.count()).select_from(PositionCache))).scalar_one()
    assert total == 1


async def test_deserializes_the_cached_result_correctly(db_session: AsyncSession) -> None:
    fake_engine = FakeEngine([_line(cp=123)])
    cached_engine = CachedEngineBridge(db_session, fake_engine, "stockfish")
    board = chess.Board()

    await cached_engine.analyze(board)
    lines = await cached_engine.analyze(board)  # esta viene de la caché

    assert lines[0]["score"].white().score() == 123
    assert lines[0]["pv"][0] == chess.Move.from_uci("e2e4")


async def test_caches_the_engine_win_draw_loss(db_session: AsyncSession) -> None:
    """RF-2.6: la W/D/L del motor viaja en el mismo JSON que la puntuación, así
    que una posición rescatada de la caché la conserva. Si no, reabrir una
    partida analizada perdería justo la segunda opinión que la distingue."""
    fake_engine = FakeEngine([_line(cp=20, wdl=(742, 163, 95))])
    cached_engine = CachedEngineBridge(db_session, fake_engine, "lc0")
    board = chess.Board()

    await cached_engine.analyze(board)
    lines = await cached_engine.analyze(board)  # esta viene de la caché

    cached_wdl = lines[0]["wdl"].white()
    assert (cached_wdl.wins, cached_wdl.draws, cached_wdl.losses) == (742, 163, 95)


async def test_a_line_cached_before_rf_2_6_still_works(db_session: AsyncSession) -> None:
    """Toda la caché escrita antes de pedirle la W/D/L al motor carece de esa
    clave. Leerla tiene que seguir funcionando y dar simplemente "no la hay":
    una línea sin W/D/L es válida, no un error."""
    fake_engine = FakeEngine([_line(cp=55)])
    cached_engine = CachedEngineBridge(db_session, fake_engine, "stockfish")
    board = chess.Board()

    await cached_engine.analyze(board)
    cached_row = (await db_session.execute(select(PositionCache))).scalars().one()
    assert "wdl" not in cached_row.lines_json[0]

    lines = await cached_engine.analyze(board)
    assert lines[0]["score"].white().score() == 55
    assert lines[0].get("wdl") is None


async def test_caches_mate_correctly(db_session: AsyncSession) -> None:
    fake_engine = FakeEngine([_line(mate=3)])
    cached_engine = CachedEngineBridge(db_session, fake_engine, "stockfish")
    board = chess.Board()

    await cached_engine.analyze(board)
    lines = await cached_engine.analyze(board)

    assert lines[0]["score"].white().mate() == 3


async def test_different_positions_do_not_share_cache(db_session: AsyncSession) -> None:
    fake_engine = FakeEngine([_line()])
    cached_engine = CachedEngineBridge(db_session, fake_engine, "stockfish")

    starting_board = chess.Board()
    board_after_e4 = chess.Board()
    board_after_e4.push_uci("e2e4")

    await cached_engine.analyze(starting_board)
    await cached_engine.analyze(board_after_e4)

    assert fake_engine.calls == 2


async def test_time_limit_is_not_cached(db_session: AsyncSession) -> None:
    """Dos búsquedas de "un segundo" no exploran lo mismo según la carga de la
    máquina, así que no son intercambiables."""
    fake_engine = FakeEngine([_line()], limit_kind="time")
    cached_engine = CachedEngineBridge(db_session, fake_engine, "stockfish")
    board = chess.Board()

    await cached_engine.analyze(board)
    await cached_engine.analyze(board)

    assert fake_engine.calls == 2


async def test_node_limit_is_cached(db_session: AsyncSession) -> None:
    """N nodos siempre son N nodos: es determinista, y Lc0 (que va por nodos y
    es lento) es justo quien más necesita la caché."""
    fake_engine = FakeEngine([_line()], limit_kind="nodes")
    cached_engine = CachedEngineBridge(db_session, fake_engine, "lc0")
    board = chess.Board()

    await cached_engine.analyze(board)
    await cached_engine.analyze(board)

    assert fake_engine.calls == 1


async def test_changing_the_lc0_network_invalidates_the_cache(db_session: AsyncSession) -> None:
    """La misma posición evaluada por Lc0 con otra red da otro resultado; sin
    incluir la red en la clave, la caché devolvería el de la red anterior."""
    board = chess.Board()

    engine_with_network_a = FakeEngine([_line(cp=10)], weights="/redes/red-a.pb.gz")
    await CachedEngineBridge(db_session, engine_with_network_a, "lc0").analyze(board)

    engine_with_network_b = FakeEngine([_line(cp=90)], weights="/redes/red-b.pb.gz")
    lines = await CachedEngineBridge(db_session, engine_with_network_b, "lc0").analyze(board)

    assert engine_with_network_b.calls == 1  # no reutilizó lo de la otra red
    assert lines[0]["score"].white().score() == 90

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


def _line(cp: int = 40, mate: int | None = None) -> chess.engine.InfoDict:
    score = chess.engine.Mate(mate) if mate is not None else chess.engine.Cp(cp)
    return {
        "score": chess.engine.PovScore(score, chess.WHITE),
        "pv": [chess.Move.from_uci("e2e4")],
    }


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

import chess
import chess.engine
import pytest
from lucia_core.engine import EngineBridge, EngineConfig

from .conftest import STOCKFISH_PATH, requires_stockfish


def _config(**overrides: object) -> EngineConfig:
    base = {"name": "stockfish", "path": STOCKFISH_PATH, "limit_kind": "depth", "limit_value": 8}
    base.update(overrides)
    return EngineConfig(**base)


@requires_stockfish
async def test_analyzes_the_starting_position_with_a_single_line() -> None:
    async with EngineBridge(_config(multipv=1)) as engine:
        engine_lines = await engine.analyze(chess.Board())

    assert len(engine_lines) == 1
    assert engine_lines[0]["pv"][0] in chess.Board().legal_moves


@requires_stockfish
async def test_multipv_returns_several_ordered_lines() -> None:
    async with EngineBridge(_config(multipv=3)) as engine:
        engine_lines = await engine.analyze(chess.Board())

    assert len(engine_lines) == 3
    evals = [engine_line["score"].white().score(mate_score=100_000) for engine_line in engine_lines]
    assert evals == sorted(evals, reverse=True)  # blancas mueven: mejor línea primero


@requires_stockfish
async def test_detects_mate_in_a_forced_position() -> None:
    # Mate en 1 para las blancas (Re1-e8#), verificado con
    # `board.is_checkmate()` antes de fijarlo como fixture.
    mate_in_one_board = chess.Board("6k1/5ppp/8/8/8/8/8/4R2K w - - 0 1")
    async with EngineBridge(_config(multipv=1)) as engine:
        engine_lines = await engine.analyze(mate_in_one_board)

    score = engine_lines[0]["score"].white()
    assert score.is_mate()
    assert score.mate() == 1


async def test_analyzing_without_opening_the_engine_fails_clearly() -> None:
    engine = EngineBridge(_config())
    with pytest.raises(RuntimeError):
        await engine.analyze(chess.Board())


@requires_stockfish
async def test_only_sends_options_the_engine_declares() -> None:
    """Lc0 no soporta `Hash` (usa `NNCacheSize`, que ni siquiera se mide en
    MB). Mandarle una opción desconocida aborta la conexión, así que las
    genéricas se filtran contra las que el motor declara."""
    async with EngineBridge(_config()) as engine:
        options = engine._options_to_apply()

    assert "Threads" in options  # Stockfish sí la declara
    assert set(options) <= set(engine.config.extra_options) | {
        "Threads",
        "Hash",
        "UCI_ShowWDL",
    }


@requires_stockfish
async def test_asks_the_engine_for_its_win_draw_loss() -> None:
    """RF-2.6: la W/D/L la informa el motor solo si se le enciende
    `UCI_ShowWDL`, y sin ella `python-chess` no la trae en las líneas. Es lo
    que distingue la opinión del motor de la fórmula sobre el centipeón."""
    async with EngineBridge(_config(multipv=1)) as engine:
        assert engine._options_to_apply()["UCI_ShowWDL"] is True
        engine_lines = await engine.analyze(chess.Board())

    wdl = engine_lines[0]["wdl"].white()
    assert wdl.wins + wdl.draws + wdl.losses == 1000


@requires_stockfish
async def test_extra_options_are_not_filtered() -> None:
    """A diferencia de las genéricas, una `extra_option` la pidió alguien a
    propósito: si el motor no la conoce, debe fallar y notarse."""
    config = _config(extra_options={"OpcionQueNoExiste": 1})
    with pytest.raises(chess.engine.EngineError):
        async with EngineBridge(config):
            pass

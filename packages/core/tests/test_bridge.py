import chess
import chess.engine
import pytest
from lucia_core.engine import EngineBridge, EngineConfig

from .conftest import STOCKFISH_PATH, requiere_stockfish


def _config(**overrides: object) -> EngineConfig:
    base = {"name": "stockfish", "path": STOCKFISH_PATH, "limit_kind": "depth", "limit_value": 8}
    base.update(overrides)
    return EngineConfig(**base)


@requiere_stockfish
async def test_analiza_posicion_inicial_con_una_sola_linea() -> None:
    async with EngineBridge(_config(multipv=1)) as motor:
        lineas = await motor.analyse(chess.Board())

    assert len(lineas) == 1
    assert lineas[0]["pv"][0] in chess.Board().legal_moves


@requiere_stockfish
async def test_multipv_devuelve_varias_lineas_ordenadas() -> None:
    async with EngineBridge(_config(multipv=3)) as motor:
        lineas = await motor.analyse(chess.Board())

    assert len(lineas) == 3
    evals = [linea["score"].white().score(mate_score=100_000) for linea in lineas]
    assert evals == sorted(evals, reverse=True)  # blancas mueven: mejor línea primero


@requiere_stockfish
async def test_detecta_mate_en_una_posicion_forzada() -> None:
    # Mate en 1 para las blancas (Re1-e8#), verificado con
    # `board.is_checkmate()` antes de fijarlo como fixture.
    tablero = chess.Board("6k1/5ppp/8/8/8/8/8/4R2K w - - 0 1")
    async with EngineBridge(_config(multipv=1)) as motor:
        lineas = await motor.analyse(tablero)

    score = lineas[0]["score"].white()
    assert score.is_mate()
    assert score.mate() == 1


async def test_analizar_sin_abrir_el_motor_falla_claro() -> None:
    motor = EngineBridge(_config())
    with pytest.raises(RuntimeError):
        await motor.analyse(chess.Board())


@requiere_stockfish
async def test_solo_manda_opciones_que_el_motor_declara() -> None:
    """Lc0 no soporta `Hash` (usa `NNCacheSize`, que ni siquiera se mide en
    MB). Mandarle una opción desconocida aborta la conexión, así que las
    genéricas se filtran contra las que el motor declara."""
    async with EngineBridge(_config()) as motor:
        opciones = motor._opciones_a_aplicar()

    assert "Threads" in opciones  # Stockfish sí la declara
    assert set(opciones) <= set(motor.config.extra_options) | {"Threads", "Hash"}


@requiere_stockfish
async def test_las_extra_options_no_se_filtran() -> None:
    """A diferencia de las genéricas, una `extra_option` la pidió alguien a
    propósito: si el motor no la conoce, debe fallar y notarse."""
    config = _config(extra_options={"OpcionQueNoExiste": 1})
    with pytest.raises(chess.engine.EngineError):
        async with EngineBridge(config):
            pass

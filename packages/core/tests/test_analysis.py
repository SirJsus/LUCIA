import chess
from lucia_core.analysis import analyze_game, evaluate_positions
from lucia_core.engine import EngineBridge, EngineConfig

from .conftest import STOCKFISH_PATH, requiere_stockfish

# Fool's mate: negras dan mate en la jugada 2. Corta a propósito para que el
# test sea rápido, y con un blunder final evidente (Qh4## era evitable).
JUGADAS = ["f2f3", "e7e5", "g2g4", "d8h4"]


def _config(**overrides: object) -> EngineConfig:
    base = {
        "name": "stockfish",
        "path": STOCKFISH_PATH,
        "limit_kind": "depth",
        "limit_value": 10,
        "multipv": 1,
    }
    base.update(overrides)
    return EngineConfig(**base)


@requiere_stockfish
async def test_evaluate_positions_produce_n_mas_1_posiciones() -> None:
    board = chess.Board()
    moves = [chess.Move.from_uci(u) for u in JUGADAS]

    async with EngineBridge(_config()) as motor:
        posiciones = await evaluate_positions(motor, board, moves)

    assert len(posiciones) == len(moves) + 1
    assert posiciones[0].fen.startswith(chess.STARTING_FEN.split(" ")[0])
    assert posiciones[0].turn == chess.WHITE
    assert posiciones[-1].turn == chess.WHITE  # tras 2 jugadas de cada color


@requiere_stockfish
async def test_analyze_game_clasifica_el_blunder_final() -> None:
    board = chess.Board()
    moves = [chess.Move.from_uci(u) for u in JUGADAS]

    async with EngineBridge(_config()) as motor:
        resultado = await analyze_game(motor, board, moves)

    assert len(resultado.moves) == 4
    # g2g4 (blancas) abre la puerta a Qh4#: debería salir mal clasificado.
    jugada_g4 = resultado.moves[2]
    assert jugada_g4.uci == "g2g4"
    assert jugada_g4.classification in {"mistake", "blunder"}
    assert resultado.white_accuracy < 90  # el blunder tiene que notarse

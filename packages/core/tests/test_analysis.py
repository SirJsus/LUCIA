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


class MotorQueSeQueja:
    """Motor falso que falla si se le pide analizar una posición terminada,
    que es justo lo que hacía colgarse a Lc0."""

    def __init__(self) -> None:
        self.llamadas = 0

    async def analyse(self, board: chess.Board) -> list[dict]:
        if board.is_game_over():
            raise AssertionError("no se debe consultar al motor en una posición terminal")
        self.llamadas += 1
        return [
            {
                "score": chess.engine.PovScore(chess.engine.Cp(10), board.turn),
                "pv": [next(iter(board.legal_moves))],
            }
        ]


async def test_no_consulta_al_motor_en_posiciones_terminales() -> None:
    """Lc0 se queda colgado si se le pide `go` en una posición sin jugadas
    legales, así que cualquier partida acabada en mate dejaba tieso el
    análisis."""
    board = chess.Board()
    # Mate del pastor: la última posición es jaque mate.
    jugadas = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
    moves = [chess.Move.from_uci(u) for u in jugadas]

    motor = MotorQueSeQueja()
    posiciones = await evaluate_positions(motor, board, moves)

    assert len(posiciones) == len(moves) + 1
    assert motor.llamadas == len(moves)  # una menos: la final no se consulta

    final = posiciones[-1]
    assert final.best_move is None
    assert final.score.pov(final.turn).is_mate()


async def test_las_tablas_terminales_valen_cero() -> None:
    # Rey ahogado: sin jugadas legales pero sin jaque.
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    posiciones = await evaluate_positions(MotorQueSeQueja(), board, [])

    assert board.is_stalemate()
    assert posiciones[0].score.pov(chess.WHITE).score() == 0

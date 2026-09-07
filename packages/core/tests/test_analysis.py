import chess
from lucia_core.analysis import analyze_game, evaluate_positions
from lucia_core.engine import EngineBridge, EngineConfig

from .conftest import STOCKFISH_PATH, requires_stockfish

# Fool's mate: negras dan mate en la jugada 2. Corta a propósito para que el
# test sea rápido, y con un blunder final evidente (Qh4## era evitable).
FOOLS_MATE_UCI_MOVES = ["f2f3", "e7e5", "g2g4", "d8h4"]


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


@requires_stockfish
async def test_evaluate_positions_returns_n_plus_1_positions() -> None:
    board = chess.Board()
    moves = [chess.Move.from_uci(uci) for uci in FOOLS_MATE_UCI_MOVES]

    async with EngineBridge(_config()) as engine:
        position_evals = await evaluate_positions(engine, board, moves)

    assert len(position_evals) == len(moves) + 1
    assert position_evals[0].fen.startswith(chess.STARTING_FEN.split(" ")[0])
    assert position_evals[0].turn == chess.WHITE
    assert position_evals[-1].turn == chess.WHITE  # tras 2 jugadas de cada color


@requires_stockfish
async def test_analyze_game_classifies_the_final_blunder() -> None:
    board = chess.Board()
    moves = [chess.Move.from_uci(uci) for uci in FOOLS_MATE_UCI_MOVES]

    async with EngineBridge(_config()) as engine:
        analyzed_game = await analyze_game(engine, board, moves)

    assert len(analyzed_game.moves) == 4
    # g2g4 (blancas) abre la puerta a Qh4#: debería salir mal clasificado.
    g4_move = analyzed_game.moves[2]
    assert g4_move.uci == "g2g4"
    assert g4_move.classification in {"mistake", "blunder"}
    assert analyzed_game.white_accuracy < 90  # el blunder tiene que notarse


class EngineRejectingTerminalPositions:
    """Motor falso que falla si se le pide analizar una posición terminada,
    que es justo lo que hacía colgarse a Lc0."""

    def __init__(self) -> None:
        self.analyze_calls = 0

    async def analyze(self, board: chess.Board) -> list[dict]:
        if board.is_game_over():
            raise AssertionError("no se debe consultar al motor en una posición terminal")
        self.analyze_calls += 1
        return [
            {
                "score": chess.engine.PovScore(chess.engine.Cp(10), board.turn),
                "pv": [next(iter(board.legal_moves))],
            }
        ]


async def test_does_not_query_the_engine_on_terminal_positions() -> None:
    """Lc0 se queda colgado si se le pide `go` en una posición sin jugadas
    legales, así que cualquier partida acabada en mate dejaba tieso el
    análisis."""
    board = chess.Board()
    # Mate del pastor: la última posición es jaque mate.
    scholars_mate_uci_moves = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
    moves = [chess.Move.from_uci(uci) for uci in scholars_mate_uci_moves]

    engine = EngineRejectingTerminalPositions()
    position_evals = await evaluate_positions(engine, board, moves)

    assert len(position_evals) == len(moves) + 1
    assert engine.analyze_calls == len(moves)  # una menos: la final no se consulta

    final = position_evals[-1]
    assert final.best_move is None
    assert final.score.pov(final.turn).is_mate()


async def test_terminal_draws_score_zero() -> None:
    # Rey ahogado: sin jugadas legales pero sin jaque.
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    position_evals = await evaluate_positions(EngineRejectingTerminalPositions(), board, [])

    assert board.is_stalemate()
    assert position_evals[0].score.pov(chess.WHITE).score() == 0

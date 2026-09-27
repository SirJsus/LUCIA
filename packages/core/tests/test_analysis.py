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


@requires_stockfish
async def test_evaluate_positions_keeps_every_multipv_line() -> None:
    """Con MultiPV > 1 se guardan todas las líneas, no solo la mejor: son las
    alternativas de cada jugada (RF-10.1)."""
    board = chess.Board()
    moves = [chess.Move.from_uci(uci) for uci in FOOLS_MATE_UCI_MOVES]

    async with EngineBridge(_config(multipv=3)) as engine:
        position_evals = await evaluate_positions(engine, board, moves)

    opening = position_evals[0]
    assert len(opening.lines) == 3
    # Ordenadas de mejor a peor, y la primera es la que ya devolvían
    # `best_move` y `pv`.
    assert opening.best_move == opening.lines[0].move
    assert opening.pv == opening.lines[0].pv
    assert opening.score == opening.lines[0].score
    # Cada línea propone una jugada distinta: son alternativas de verdad.
    assert len({line.move for line in opening.lines}) == 3


@requires_stockfish
async def test_analyzed_move_carries_the_alternatives_of_the_previous_position() -> None:
    board = chess.Board()
    moves = [chess.Move.from_uci(uci) for uci in FOOLS_MATE_UCI_MOVES]

    async with EngineBridge(_config(multipv=3)) as engine:
        analyzed_game = await analyze_game(engine, board, moves)

    blunder = analyzed_game.moves[2]  # g2g4
    assert blunder.uci == "g2g4"
    # Las alternativas son las de la posición desde la que se jugó, así que la
    # primera es la jugada que el motor recomendaba en su lugar.
    assert blunder.alternatives[0].move is not None
    assert blunder.alternatives[0].move.uci() == blunder.best_move_uci
    assert len(blunder.alternatives) == 3


class BookEngine:
    """Motor falso que siempre ve la posición equilibrada: así la clasificación
    de las primeras jugadas solo puede venir del libro de aperturas."""

    async def analyze(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        return [{"score": chess.engine.PovScore(chess.engine.Cp(10), board.turn), "pv": []}]


async def test_moves_still_in_theory_are_classified_as_book() -> None:
    """RF-2.2: mientras la partida siga en la tabla ECO, la jugada es teoría y
    no un acierto de quien la juega."""
    board = chess.Board()
    italian = board.copy()
    for san in ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "c3", "Nf6"):
        italian.push_san(san)
    moves = list(italian.move_stack)

    analyzed_game = await analyze_game(BookEngine(), board, moves)

    # Las ocho son teoría conocida: la italiana está en la tabla hasta el final
    # de esta línea, así que ninguna se puntúa como acierto del jugador.
    assert [move.classification for move in analyzed_game.moves] == ["book"] * 8


async def test_moves_out_of_theory_are_classified_by_evaluation() -> None:
    """En cuanto la partida se sale del repertorio, vuelve a mandar el motor."""
    board = chess.Board()
    off_book = board.copy()
    for san in ("a3", "h6", "b3", "g5", "c3", "f6"):
        off_book.push_san(san)

    analyzed_game = await analyze_game(BookEngine(), board, list(off_book.move_stack))

    classifications = [move.classification for move in analyzed_game.moves]
    assert classifications[0] == "book"  # "1. a3" tiene nombre
    assert "book" not in classifications[2:]

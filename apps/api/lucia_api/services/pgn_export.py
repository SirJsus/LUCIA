"""Exportación de una partida analizada a PGN anotado (RF-5.5).

Sale el PGN original de la partida con lo que el análisis añadió encima: un
símbolo de notación (`?!`, `?`, `??`) en las jugadas que fallaron, un
comentario por jugada con su clasificación y la probabilidad de victoria que
dejó, y —donde el motor prefería otra cosa— su línea principal como variante.

No vuelve a preguntarle nada al motor: todo lo que escribe está ya en
`analyzed_moves` (RF-2.2, RF-10.1). El resultado se abre en lichess,
ChessBase o SCID como cualquier otro PGN comentado.
"""

from __future__ import annotations

import io

import chess
import chess.pgn

from lucia_api.db.models import Analysis, AnalyzedMove, Game
from lucia_api.services.analysis import alternatives_of, engine_lines_from_serialized

#: Cuántas jugadas de la línea del motor se escriben como variante, como
#: máximo (si la línea guardada es más corta, se escribe entera). La línea
#: entera suele pasar de veinte y, más allá de las primeras, es una predicción
#: que nadie va a seguir: lo que se quiere ver es qué se debía haber jugado y
#: cómo seguía la idea.
MAX_VARIATION_PLIES = 6

#: Etiqueta de cada clasificación (RF-2.2) tal como se escribe en el PGN.
#: Son las mismas que enseña la interfaz en `apps/web/src/lib/classification.ts`,
#: escritas aquí porque el PGN lo compone el servidor: si cambian allí, cambian
#: aquí (criterio C-5 de docs/07-coherencia-ui.md).
CLASSIFICATION_COMMENT_LABELS = {
    "best": "Mejor jugada",
    "excellent": "Excelente",
    "good": "Buena",
    "book": "Teoría",
    "inaccuracy": "Imprecisión",
    "mistake": "Error",
    "blunder": "Blunder",
    "missed_win": "Perdió el mate",
}

#: Símbolo de notación por clasificación, en el código numérico que el
#: estándar PGN llama NAG. Solo lo llevan las jugadas que fallaron: marcar con
#: `!` una jugada que simplemente coincidió con el motor sería atribuirle un
#: mérito que el análisis no mide. "Perdió el mate" comparte el `??` de blunder
#: porque no hay NAG para "tenía ganada y la soltó".
CLASSIFICATION_NAGS = {
    "inaccuracy": chess.pgn.NAG_DUBIOUS_MOVE,  # ?!
    "mistake": chess.pgn.NAG_MISTAKE,  # ?
    "blunder": chess.pgn.NAG_BLUNDER,  # ??
    "missed_win": chess.pgn.NAG_BLUNDER,
}


def export_annotated_pgn(
    game: Game,
    analysis: Analysis,
    moves: list[AnalyzedMove],
    cached_alternatives: dict[int, list[dict]],
) -> str:
    """El PGN de `game` con las anotaciones de `analysis` (RF-5.5).

    `cached_alternatives` es lo que `services.analysis.alternatives_from_cache`
    rescató para los análisis anteriores a RF-10.1, que no guardaron sus
    líneas; las jugadas que no tengan ninguna salen comentadas pero sin
    variante.
    """
    exported_game = chess.pgn.read_game(io.StringIO(game.pgn))
    if exported_game is None:
        raise ValueError("la partida no tiene un PGN legible")

    _write_annotation_headers(exported_game.headers, analysis)
    analyzed_by_ply = {move.ply: move for move in moves}

    node = exported_game
    ply = 0
    while node.variations:
        # `variations[0]` es la partida tal como se jugó; las variantes que
        # este exportador añade cuelgan detrás y no se recorren.
        node = node.variations[0]
        analyzed_move = analyzed_by_ply.get(ply)
        if analyzed_move is not None:
            _annotate_move_node(node, analyzed_move, cached_alternatives)
        ply += 1

    return str(exported_game)


def _write_annotation_headers(headers: chess.pgn.Headers, analysis: Analysis) -> None:
    """Quién anotó la partida y con qué, en las cabeceras.

    `Annotator` es del estándar; las dos de precisión no lo son, pero un lector
    que no las conozca las ignora y quien abra el archivo en un editor de texto
    ve de un vistazo con qué se analizó.
    """
    headers["Annotator"] = f"LUCIA · {analysis.engine} profundidad {analysis.depth}"
    if analysis.white_accuracy is not None:
        headers["WhiteAccuracy"] = f"{analysis.white_accuracy:.1f}"
    if analysis.black_accuracy is not None:
        headers["BlackAccuracy"] = f"{analysis.black_accuracy:.1f}"


def _annotate_move_node(
    node: chess.pgn.ChildNode,
    analyzed_move: AnalyzedMove,
    cached_alternatives: dict[int, list[dict]],
) -> None:
    """Pone en una jugada su símbolo, su comentario y, si el motor prefería
    otra cosa, su línea principal como variante."""
    nag = CLASSIFICATION_NAGS.get(analyzed_move.classification)
    if nag is not None:
        node.nags.add(nag)

    board_before = chess.Board(analyzed_move.fen_before)
    better_move = (
        None
        if analyzed_move.best_move_uci == analyzed_move.uci
        else _legal_best_move(analyzed_move, board_before)
    )
    node.comment = _format_move_comment(analyzed_move, board_before, better_move)

    if better_move is not None:
        _add_engine_variation(node, analyzed_move, cached_alternatives)


def _format_move_comment(
    analyzed_move: AnalyzedMove, board_before: chess.Board, better_move: chess.Move | None
) -> str:
    """El comentario de una jugada: qué fue y cómo dejó la partida.

    La probabilidad de victoria va **desde el punto de vista de las blancas**,
    como todo lo que LUCIA enseña, y lleva dicho de quién es: un "45 %" a secas
    no comunica nada (criterios C-5 y C-6 de docs/07-coherencia-ui.md). En la
    base está desde el punto de vista de quien jugó, así que aquí se gira.
    """
    label = CLASSIFICATION_COMMENT_LABELS.get(
        analyzed_move.classification, analyzed_move.classification
    )
    win_percent_white = analyzed_move.win_percent_after
    if analyzed_move.color == "black":
        win_percent_white = 100 - win_percent_white

    parts = [label, f"{win_percent_white:.0f} % prob. victoria blancas"]
    if better_move is not None:
        parts.append(f"mejor {_numbered_san(board_before, better_move, analyzed_move.ply)}")
    return " · ".join(parts)


def _legal_best_move(analyzed_move: AnalyzedMove, board_before: chess.Board) -> chess.Move | None:
    """La jugada que el motor prefería, o `None` si el análisis no la guardó o
    no es legal en la posición (un análisis viejo de otra partida)."""
    if analyzed_move.best_move_uci is None:
        return None
    try:
        move = chess.Move.from_uci(analyzed_move.best_move_uci)
    except ValueError:
        return None
    return move if move in board_before.legal_moves else None


def _add_engine_variation(
    node: chess.pgn.ChildNode,
    analyzed_move: AnalyzedMove,
    cached_alternatives: dict[int, list[dict]],
) -> None:
    """Cuelga la línea principal del motor como variante hermana de la jugada.

    Se añade al **padre**, que es la posición desde la que se eligió: una
    variante es otra forma de seguir desde ahí, no una continuación de lo que
    se jugó.
    """
    serialized_lines = alternatives_of(analyzed_move, cached_alternatives)
    if not serialized_lines:
        return

    best_line = engine_lines_from_serialized(serialized_lines, analyzed_move.fen_before)[0]
    # `pv_san` ya viene recortada a las jugadas legales desde `fen_before`
    # (`services.analysis`), así que sirve de medida: lo que no se pudo nombrar
    # tampoco se puede jugar, y `add_line` con una jugada ilegal dejaría el PGN
    # corrupto sin avisar.
    legal_plies = min(len(best_line.pv_san), MAX_VARIATION_PLIES)
    if legal_plies:
        node.parent.add_line(chess.Move.from_uci(uci) for uci in best_line.pv_uci[:legal_plies])


def _numbered_san(board_before: chess.Board, move: chess.Move, ply: int) -> str:
    """La jugada con su número, como se cita una jugada en texto: "13.Be3" o
    "13...Bxf3". El número sale del ply y no del tablero para que sirva igual
    en una partida que empieza desde una posición cualquiera."""
    move_number = ply // 2 + 1
    separator = "." if ply % 2 == 0 else "..."
    return f"{move_number}{separator}{board_before.san(move)}"

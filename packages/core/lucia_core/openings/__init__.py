"""Clasificación de aperturas por posición, con la tabla ECO de Lichess.

La tabla viene de chess-openings de Lichess (CC0, dominio público) y se versiona
ya procesada en `data/openings.tsv`: una fila por posición conocida, con su
código ECO y su nombre. La genera `scripts/build-openings-table.py`, que es
donde está contado el porqué del formato.

**Se busca por posición, no por secuencia de jugadas.** Es lo que hace que las
transposiciones funcionen: llegar a la Defensa Siciliana por otro orden de
jugadas es la misma posición, y sale con el mismo nombre. La clave es el EPD
—el FEN sin los contadores—, porque la misma posición alcanzada en la jugada 4
o en la 6 tiene que valer igual.

Para qué se usa:

- **Nombrar la apertura de una partida** sin depender de lo que reporte
  chess.com, que no la trae en todas (RF-3.2).
- **La categoría "book" de `classify_move`** (RF-2.2): mientras la partida siga
  en una posición conocida, la jugada es teoría y no tiene sentido puntuarla
  como acierto o error del jugador.

**La tabla tiene huecos, y hay que contar con ellos.** Solo nombra las
posiciones en las que termina alguna línea con nombre, así que en mitad de una
Najdorf hay jugadas sin nombre —después de `Nxd4` no acaba ninguna apertura— y
dos jugadas más adelante vuelve a haberlo. Por eso la búsqueda no se para en el
primer hueco: sigue y se queda con la posición conocida **más profunda**. Lo
que sí la termina es una racha de posiciones desconocidas, que ya no es un
hueco sino haberse salido del repertorio — y eso es lo que hace que la
evaluación al salir de la apertura (RF-3.2) signifique algo.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chess
import chess.pgn

DATA_PATH = Path(__file__).parent / "data" / "openings.tsv"

#: Hasta dónde se busca apertura. Más allá de la jugada 15, lo que se reconozca
#: es una transposición casual, no repertorio.
MAX_BOOK_PLIES = 30

#: Cuántas posiciones seguidas sin nombre se toleran antes de dar la teoría por
#: terminada. Cuatro cubre los huecos reales de la tabla —lo normal es uno o
#: dos— sin llegar a llamar "libro" a media partida.
MAX_UNKNOWN_PLIES_IN_A_ROW = 4


@dataclass(frozen=True)
class Opening:
    """Una apertura de la tabla ECO."""

    eco: str
    """Código ECO ("B90"), el que usan las bases de datos de ajedrez."""
    name: str
    """Nombre en inglés, tal como lo publica Lichess: "Sicilian Defense:
    Najdorf Variation". No se traduce: son los nombres con los que el usuario
    los va a encontrar en cualquier otro sitio."""


@lru_cache(maxsize=1)
def default_book() -> dict[str, Opening]:
    """La tabla ECO cargada en memoria, indexada por posición (EPD).

    Se cachea porque son casi cuatro mil posiciones y no cambia en tiempo de
    ejecución: quien la pida dos veces recibe la misma.
    """
    with DATA_PATH.open(encoding="utf-8") as data:
        rows = csv.DictReader((line for line in data if not line.startswith("#")), delimiter="\t")
        return {row["epd"]: Opening(eco=row["eco"], name=row["name"]) for row in rows}


@dataclass(frozen=True)
class GameOpening:
    """Hasta dónde llegó la teoría en una partida, y cómo se llama."""

    opening: Opening | None
    """La apertura más específica que se reconoció, o `None` si la partida se
    salió de la teoría desde la primera jugada (o empezó en una posición que no
    es la estándar)."""
    book_plies: int
    """Hasta qué jugada llega la teoría: el ply de la posición conocida más
    profunda. Las jugadas anteriores cuentan como libro aunque alguna posición
    intermedia no tenga nombre."""


def identify_opening(board: chess.Board, moves: list[chess.Move]) -> GameOpening:
    """Recorre la partida y devuelve su apertura y cuándo se salió del libro.

    Se queda con la posición conocida **más profunda**, que es la que da el
    nombre más específico: "Siciliana: Najdorf" dice más que "Siciliana". Los
    huecos de la tabla no cortan la búsqueda, pero una racha de posiciones
    desconocidas sí (ver `MAX_UNKNOWN_PLIES_IN_A_ROW`).
    """
    book = default_book()
    current_board = board.copy()
    deepest_opening: Opening | None = None
    book_plies = 0
    unknown_plies_in_a_row = 0

    for ply, move in enumerate(moves[:MAX_BOOK_PLIES], start=1):
        current_board.push(move)
        opening = book.get(current_board.epd())
        if opening is None:
            unknown_plies_in_a_row += 1
            if unknown_plies_in_a_row > MAX_UNKNOWN_PLIES_IN_A_ROW:
                break
            continue
        unknown_plies_in_a_row = 0
        deepest_opening, book_plies = opening, ply

    return GameOpening(opening=deepest_opening, book_plies=book_plies)


def opening_of_pgn(pgn_text: str) -> Opening | None:
    """La apertura de una partida escrita en PGN.

    Es lo que necesita quien tiene la partida en texto y no en jugadas: el
    importador de chess.com al guardarla y la migración que nombró las que ya
    estaban guardadas.

    `None` si el PGN no se puede leer o si la partida no empieza donde empieza
    la teoría —una con ventaja o de Chess960 no tiene apertura ECO, y nombrarla
    sería inventar—.
    """
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return None
    return identify_opening(game.board(), list(game.mainline_moves())).opening

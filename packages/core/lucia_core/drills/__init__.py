"""Drill de aperturas (RF-4.2): repetir jugando las líneas donde peor se rinde.

Un drill es **una línea concreta** —las jugadas de los dos bandos desde la
posición inicial— que se repite jugando el bando propio: la aplicación
responde por el rival y hay que acertar cada jugada propia. No es un puzzle de
una posición suelta (eso es RF-4.1): lo que se entrena es la línea entera, que
es como se olvida y como se recuerda una apertura.

Aquí viven las reglas puras —por dónde va la línea, qué jugada toca, cuándo se
acabó y qué cuenta como "rendir peor"—, sin base de datos, sin motor y sin
reloj, para poder probarse solas (RNF-8). Quien carga el material y lo guarda
es `lucia_api.services.drills`.

**Cuándo vuelve un drill no se decide aquí**: lo decide el mismo SM-2 de
`lucia_core.training` que ya reparte los puzzles. Un drill se repasa como se
repasa un puzzle, así que no hay dos algoritmos de repaso que mantener ni dos
comportamientos que explicar.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import chess

#: Cuántas partidas hacen falta para que una línea entre en el drill. Con una
#: o dos, un mal marcador es mala suerte y no un agujero de repertorio: la
#: pregunta de RF-4.2 es de hábito ("esto lo hago ocho veces y saco un 25 %"),
#: la misma que ya se hace el repertorio de RF-3.6.
MIN_GAMES_TO_DRILL = 3

#: Con qué puntuación se considera que una línea ni gana ni pierde. Es el
#: marcador de partir la diferencia, y el punto desde el que se mide lo que
#: una línea cuesta.
EVEN_SCORE_PERCENT = 50.0


@dataclass(frozen=True)
class DrillLine:
    """La línea que hay que reproducir y de qué bando se juega.

    `moves_uci` lleva las jugadas de **los dos bandos** en orden desde la
    posición inicial. Las del rival las juega la aplicación; las propias son
    las que hay que acertar. La última jugada de la línea es siempre propia:
    una línea que acabara con la del rival pediría recordar algo que no se
    llega a jugar.
    """

    moves_uci: tuple[str, ...]
    player_color: chess.Color

    def __post_init__(self) -> None:
        if not self.moves_uci:
            raise ValueError("una línea de drill no puede estar vacía")
        if not self.is_player_ply(len(self.moves_uci) - 1):
            raise ValueError("la línea tiene que acabar en una jugada propia")

    def is_player_ply(self, ply: int) -> bool:
        """Si en esa jugada le toca mover a quien entrena. El ply 0 lo juegan
        siempre las blancas, así que el color decide la paridad."""
        return (ply % 2 == 0) == (self.player_color == chess.WHITE)

    @property
    def first_player_ply(self) -> int:
        """La primera jugada que hay que acertar: la 0 con blancas, la 1 con
        negras, porque con negras el rival abre."""
        return 0 if self.player_color == chess.WHITE else 1

    def expected_uci_at(self, ply: int) -> str:
        """La jugada propia que toca en ese punto de la línea."""
        if not self.is_player_ply(ply):
            raise ValueError(f"el ply {ply} no es una jugada propia")
        return self.moves_uci[ply]

    def reply_uci_after(self, ply: int) -> str | None:
        """Lo que contesta el rival tras la jugada propia del ply dado, o
        `None` si con ella se acabó la línea."""
        reply_ply = ply + 1
        return self.moves_uci[reply_ply] if reply_ply < len(self.moves_uci) else None

    def board_at(self, ply: int) -> chess.Board:
        """La posición con las primeras `ply` jugadas hechas: la que se ve
        cuando toca acertar la `ply`."""
        board = chess.Board()
        for uci in self.moves_uci[:ply]:
            board.push_uci(uci)
        return board

    def moves_san(self) -> list[str]:
        """La línea entera en notación algebraica, que es como se lee y como
        se enseña al terminar. No se guarda: depende de la posición, igual que
        en `lucia_core.sparring`."""
        board = chess.Board()
        return [board.san_and_push(chess.Move.from_uci(uci)) for uci in self.moves_uci]


def line_uci_from_departure(
    game_moves_uci: Sequence[str], departure_ply: int, book_move_uci: str
) -> tuple[str, ...]:
    """La línea que se repite a partir de una salida de la teoría (RF-3.6).

    Son las jugadas de la partida **hasta** el punto en el que se salió, más
    la jugada de maestros que había ahí en lugar de la que se hizo. Así el
    drill recorre la apertura tal como se jugó —que es lo que se reconoce— y
    termina justo en la decisión que costaba puntos, con la respuesta buena.

    Las jugadas propias anteriores son de libro por definición: la salida es
    la **primera** que no lo era.
    """
    return (*game_moves_uci[:departure_ply], book_move_uci)


def points_lost(games: int, score_percent: float) -> float:
    """Cuántos puntos cuesta una línea frente a partir la diferencia.

    Es la medida de "peor" de RF-4.2, y es una medida de **daño**, no de
    porcentaje: quince partidas al 40 % cuestan punto y medio, y tres al 20 %
    cuestan nueve décimas, así que es la primera la que hay que arreglar antes
    aunque su porcentaje asuste menos. Un porcentaje suelto no distingue las
    dos, y un corte absoluto ("por debajo del 45 %") deja fuera precisamente
    los agujeros de repertorio grandes, que sangran despacio y muchas veces.

    Negativo cuando la línea da puntos: entonces no hay nada que entrenar.
    """
    return games * (EVEN_SCORE_PERCENT - score_percent) / 100


def is_worth_drilling(games: int, score_percent: float) -> bool:
    """Si una línea merece entrenarse: que se repita lo bastante como para ser
    un hábito y que cueste puntos. Cuánto los cuesta es lo que ordena después
    la baraja (`points_lost`), y por eso aquí no hay más umbral que el cero:
    poner uno más alto sería decidir por quien entrena dónde está su problema.
    """
    return games >= MIN_GAMES_TO_DRILL and points_lost(games, score_percent) > 0

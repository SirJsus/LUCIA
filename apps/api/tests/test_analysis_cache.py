import chess
import chess.engine
from lucia_api.db.models import PositionCache
from lucia_api.services.analysis import CachedEngineBridge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class MotorFalso:
    """Cuenta cuántas veces se le pregunta, para probar que la caché evita
    repetir la consulta al motor real."""

    def __init__(
        self,
        respuesta: list[chess.engine.InfoDict],
        limit_kind: str = "depth",
        weights: str | None = None,
    ) -> None:
        self.llamadas = 0
        self._respuesta = respuesta
        extras = {"WeightsFile": weights} if weights else {}
        self.config = type(
            "Config",
            (),
            {
                "limit_kind": limit_kind,
                "limit_value": 10,
                "multipv": 1,
                "extra_options": extras,
            },
        )()

    async def analyse(self, board: chess.Board) -> list[chess.engine.InfoDict]:
        self.llamadas += 1
        return self._respuesta


def _linea(cp: int = 40, mate: int | None = None) -> chess.engine.InfoDict:
    puntaje = chess.engine.Mate(mate) if mate is not None else chess.engine.Cp(cp)
    return {
        "score": chess.engine.PovScore(puntaje, chess.WHITE),
        "pv": [chess.Move.from_uci("e2e4")],
    }


async def test_segunda_consulta_de_la_misma_posicion_no_llama_al_motor(
    db_session: AsyncSession,
) -> None:
    motor_falso = MotorFalso([_linea()])
    caché = CachedEngineBridge(db_session, motor_falso, "stockfish")
    board = chess.Board()

    await caché.analyse(board)
    await caché.analyse(board)

    assert motor_falso.llamadas == 1

    total = (await db_session.execute(select(func.count()).select_from(PositionCache))).scalar_one()
    assert total == 1


async def test_deserializa_el_resultado_cacheado_correctamente(db_session: AsyncSession) -> None:
    motor_falso = MotorFalso([_linea(cp=123)])
    caché = CachedEngineBridge(db_session, motor_falso, "stockfish")
    board = chess.Board()

    await caché.analyse(board)
    lineas = await caché.analyse(board)  # esta viene de la caché

    assert lineas[0]["score"].white().score() == 123
    assert lineas[0]["pv"][0] == chess.Move.from_uci("e2e4")


async def test_cachea_mate_correctamente(db_session: AsyncSession) -> None:
    motor_falso = MotorFalso([_linea(mate=3)])
    caché = CachedEngineBridge(db_session, motor_falso, "stockfish")
    board = chess.Board()

    await caché.analyse(board)
    lineas = await caché.analyse(board)

    assert lineas[0]["score"].white().mate() == 3


async def test_posiciones_distintas_no_comparten_cache(db_session: AsyncSession) -> None:
    motor_falso = MotorFalso([_linea()])
    caché = CachedEngineBridge(db_session, motor_falso, "stockfish")

    tablero1 = chess.Board()
    tablero2 = chess.Board()
    tablero2.push_uci("e2e4")

    await caché.analyse(tablero1)
    await caché.analyse(tablero2)

    assert motor_falso.llamadas == 2


async def test_limite_por_tiempo_no_se_cachea(db_session: AsyncSession) -> None:
    """Dos búsquedas de "un segundo" no exploran lo mismo según la carga de la
    máquina, así que no son intercambiables."""
    motor_falso = MotorFalso([_linea()], limit_kind="time")
    caché = CachedEngineBridge(db_session, motor_falso, "stockfish")
    board = chess.Board()

    await caché.analyse(board)
    await caché.analyse(board)

    assert motor_falso.llamadas == 2


async def test_limite_por_nodos_si_se_cachea(db_session: AsyncSession) -> None:
    """N nodos siempre son N nodos: es determinista, y Lc0 (que va por nodos y
    es lento) es justo quien más necesita la caché."""
    motor_falso = MotorFalso([_linea()], limit_kind="nodes")
    caché = CachedEngineBridge(db_session, motor_falso, "lc0")
    board = chess.Board()

    await caché.analyse(board)
    await caché.analyse(board)

    assert motor_falso.llamadas == 1


async def test_cambiar_la_red_de_lc0_invalida_la_cache(db_session: AsyncSession) -> None:
    """La misma posición evaluada por Lc0 con otra red da otro resultado; sin
    incluir la red en la clave, la caché devolvería el de la red anterior."""
    board = chess.Board()

    con_red_a = MotorFalso([_linea(cp=10)], weights="/redes/red-a.pb.gz")
    await CachedEngineBridge(db_session, con_red_a, "lc0").analyse(board)

    con_red_b = MotorFalso([_linea(cp=90)], weights="/redes/red-b.pb.gz")
    lineas = await CachedEngineBridge(db_session, con_red_b, "lc0").analyse(board)

    assert con_red_b.llamadas == 1  # no reutilizó lo de la otra red
    assert lineas[0]["score"].white().score() == 90

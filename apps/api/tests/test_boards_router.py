"""Tablero de análisis (RF-6): CRUD y análisis de una posición suelta."""

from __future__ import annotations

from collections.abc import AsyncIterator

import chess
from fastapi.testclient import TestClient
from lucia_api.db import get_session
from lucia_api.db.models import BoardVersion
from lucia_api.main import app
from lucia_api.services.boards import MAX_VERSIONS_PER_BOARD
from lucia_api.worker import AnalysisWorker
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .conftest import requires_stockfish

SAMPLE_TREE = {
    "id": "root",
    "san": None,
    "children": [{"id": "n1", "san": "e4", "uci": "e2e4", "children": []}],
}


def _override(db_session: AsyncSession) -> None:
    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session


async def test_full_cycle_create_read_update_delete(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            created = http.post(
                "/boards",
                json={"title": "Mi partida OTB", "tree_json": SAMPLE_TREE},
            )
            assert created.status_code == 201, created.text
            board_id = created.json()["id"]
            assert created.json()["root_fen"] == chess.STARTING_FEN
            assert created.json()["is_own_game"] is False

            fetched = http.get(f"/boards/{board_id}").json()
            assert fetched["tree_json"] == SAMPLE_TREE

            # Autoguardado: se manda solo lo que cambió.
            updated = http.put(
                f"/boards/{board_id}",
                json={"title": "Mi partida OTB (revisada)"},
            )
            assert updated.status_code == 200
            assert updated.json()["title"] == "Mi partida OTB (revisada)"
            assert updated.json()["tree_json"] == SAMPLE_TREE  # no se pisa

            assert len(http.get("/boards").json()) == 1

            assert http.delete(f"/boards/{board_id}").status_code == 204
            assert http.get(f"/boards/{board_id}").status_code == 404
            assert http.get("/boards").json() == []
    finally:
        app.dependency_overrides.clear()


async def test_create_from_a_fen(db_session: AsyncSession) -> None:
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/boards", json={"title": "Italiana", "root_fen": fen})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["root_fen"] == fen


async def test_invalid_fen_is_rejected_on_create(db_session: AsyncSession) -> None:
    """Guardar un FEN ilegal daría un tablero imposible de abrir después."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/boards", json={"title": "Roto", "root_fen": "esto no es un fen"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def test_update_or_delete_unknown_board_returns_404(
    db_session: AsyncSession,
) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            assert http.put("/boards/9999", json={"title": "x"}).status_code == 404
            assert http.delete("/boards/9999").status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_position_is_not_mistaken_for_an_analysis_id(db_session: AsyncSession) -> None:
    """`/analysis/position` se declara antes que `/analysis/{analysis_id}`; si
    se invirtieran, FastAPI intentaría interpretar "position" como un entero."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/analysis/position", json={"fen": "no-es-un-fen"})
    finally:
        app.dependency_overrides.clear()

    # 422 por FEN inválido, no 404 ni un error de tipo de ruta.
    assert response.status_code == 422
    assert "FEN" in response.json()["detail"]


@requires_stockfish
async def test_analyzes_a_position_and_returns_lines(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis/position",
                json={"fen": chess.STARTING_FEN, "depth": 8, "multipv": 2},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    lines = response.json()
    assert len(lines) == 2
    assert lines[0]["rank"] == 1
    assert lines[0]["pv_uci"]  # hay al menos una jugada propuesta
    assert lines[0]["pv_san"][0] in {"e4", "d4", "Nf3", "c4", "g3", "b3", "e3"}
    # La posición inicial está equilibrada: no debe haber mate.
    assert lines[0]["score_mate"] is None


@requires_stockfish
async def test_detects_mate_in_a_forced_position(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis/position",
                json={"fen": "6k1/5ppp/8/8/8/8/8/4R2K w - - 0 1", "depth": 10, "multipv": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.json()[0]["score_mate"] == 1


async def test_a_finished_position_is_not_sent_to_the_engine(db_session: AsyncSession) -> None:
    """Jaque mate y ahogado devuelven la lista vacía **sin abrir el motor**.

    No lleva `@requires_stockfish` a propósito: que pase sin motor compilado es
    justo la prueba de que no se abre ninguno. Preguntarle a Lc0 en una
    posición sin jugadas legales devuelve `bestmove a1a1`, que no es UCI
    válido y aborta la conexión; antes de la guarda, llegar al final de una
    partida terminada en mate en el tablero de análisis rompía el motor.
    """
    _override(db_session)
    checkmate = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    stalemate = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    try:
        with TestClient(app) as http:
            responses = [
                http.post("/analysis/position", json={"fen": fen}) for fen in (checkmate, stalemate)
            ]
    finally:
        app.dependency_overrides.clear()

    for response in responses:
        assert response.status_code == 200, response.text
        assert response.json() == []


async def test_excessive_depth_is_rejected(db_session: AsyncSession) -> None:
    """El análisis en vivo es síncrono: sin tope, la petición quedaría colgada."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post(
                "/analysis/position", json={"fen": chess.STARTING_FEN, "depth": 40}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def test_importing_a_pgn_can_move_the_root_position(db_session: AsyncSession) -> None:
    """Un PGN con `[FEN ...]` cambia la posición de partida del tablero
    (RF-6.7). Sin esto el listado seguiría enseñando la anterior."""
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Importado"}).json()["id"]
            response = http.put(
                f"/boards/{board_id}",
                json={"root_fen": fen, "tree_json": {"id": "root", "fen": fen, "children": []}},
            )
            listed = http.get("/boards").json()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["root_fen"] == fen
    assert listed[0]["root_fen"] == fen


async def test_invalid_fen_is_rejected_on_update(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Bueno"}).json()["id"]
            response = http.put(f"/boards/{board_id}", json={"root_fen": "ni de lejos"})
            unchanged = http.get(f"/boards/{board_id}").json()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert unchanged["root_fen"] == chess.STARTING_FEN


#: El árbol de un tablero recién creado, que es el que devuelve deshacerlo
#: todo: `BoardCreate.tree_json` no trae nada por defecto.
EMPTY_TREE: dict = {}


def _tree_with(san: str) -> dict:
    """Un árbol de una jugada. Solo importa que cada paso sea distinto del
    anterior, para reconocer a cuál vuelve el deshacer."""
    return {
        "id": "root",
        "san": None,
        "children": [{"id": san, "san": san, "uci": san, "children": []}],
    }


async def test_undo_and_redo_walk_the_history(db_session: AsyncSession) -> None:
    """RF-6.8: deshacer devuelve el árbol anterior y rehacer lo trae de vuelta."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            created = http.post("/boards", json={"title": "Historial"}).json()
            board_id = created["id"]
            # Recién creado solo existe la versión de partida: nada que deshacer.
            assert (created["can_undo"], created["can_redo"]) == (False, False)

            http.put(f"/boards/{board_id}", json={"tree_json": _tree_with("e4")})
            second = http.put(f"/boards/{board_id}", json={"tree_json": SAMPLE_TREE}).json()
            assert (second["can_undo"], second["can_redo"]) == (True, False)

            undone = http.post(f"/boards/{board_id}/undo").json()
            assert undone["tree_json"] == _tree_with("e4")
            assert (undone["can_undo"], undone["can_redo"]) == (True, True)

            redone = http.post(f"/boards/{board_id}/redo").json()
            assert redone["tree_json"] == SAMPLE_TREE
            assert redone["can_redo"] is False

            # Y el estado deshecho se lee igual desde otra petición: el
            # historial está en la base, no en la pantalla.
            http.post(f"/boards/{board_id}/undo")
            assert http.get(f"/boards/{board_id}").json()["tree_json"] == _tree_with("e4")
    finally:
        app.dependency_overrides.clear()


async def test_the_history_is_capped_and_drops_the_oldest(db_session: AsyncSession) -> None:
    """RF-6.8: pasado el tope se tiran las versiones más antiguas, nunca la
    que se está viendo ni las de al lado."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Tope"}).json()["id"]
            for number in range(MAX_VERSIONS_PER_BOARD + 5):
                http.put(f"/boards/{board_id}", json={"tree_json": _tree_with(f"m{number}")})

            kept = (
                await db_session.execute(
                    select(func.count())
                    .select_from(BoardVersion)
                    .where(BoardVersion.board_id == board_id)
                )
            ).scalar_one()
            assert kept == MAX_VERSIONS_PER_BOARD
            # Y se sigue pudiendo deshacer lo último, que es para lo que está.
            undone = http.post(f"/boards/{board_id}/undo").json()
            assert undone["tree_json"] == _tree_with(f"m{MAX_VERSIONS_PER_BOARD + 3}")
    finally:
        app.dependency_overrides.clear()


async def test_editing_after_undoing_discards_what_was_ahead(db_session: AsyncSession) -> None:
    """El historial es lineal: si se deshace y se juega otra cosa, lo que se
    había deshecho ya no lleva a ningún sitio."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Lineal"}).json()["id"]
            http.put(f"/boards/{board_id}", json={"tree_json": _tree_with("e4")})
            http.put(f"/boards/{board_id}", json={"tree_json": SAMPLE_TREE})
            http.post(f"/boards/{board_id}/undo")

            after_new_edit = http.put(
                f"/boards/{board_id}", json={"tree_json": _tree_with("d4")}
            ).json()

            assert after_new_edit["can_redo"] is False
            assert http.post(f"/boards/{board_id}/redo").status_code == 409
    finally:
        app.dependency_overrides.clear()


async def test_undoing_an_import_restores_the_starting_position(db_session: AsyncSession) -> None:
    """Importar un PGN puede mover la raíz (RF-6.7); deshacerlo la devuelve.
    Sin guardar el FEN con cada versión, el árbol viejo quedaría colgando de
    la raíz nueva."""
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Importado"}).json()["id"]
            http.put(f"/boards/{board_id}", json={"root_fen": fen, "tree_json": SAMPLE_TREE})

            undone = http.post(f"/boards/{board_id}/undo").json()
    finally:
        app.dependency_overrides.clear()

    assert undone["root_fen"] == chess.STARTING_FEN


async def test_renaming_does_not_make_history(db_session: AsyncSession) -> None:
    """Cambiar el título no es algo que se deshaga con Ctrl+Z: anotarlo
    obligaría a pulsar dos veces para retirar una jugada."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Antes"}).json()["id"]
            http.put(f"/boards/{board_id}", json={"tree_json": SAMPLE_TREE})
            renamed = http.put(f"/boards/{board_id}", json={"title": "Después"}).json()

            undone = http.post(f"/boards/{board_id}/undo").json()
    finally:
        app.dependency_overrides.clear()

    assert renamed["can_redo"] is False
    # Deshacer retira la jugada, no el renombrado.
    assert undone["title"] == "Después"
    assert undone["tree_json"] == EMPTY_TREE


async def test_nothing_to_undo_is_a_409(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Recién hecho"}).json()["id"]
            assert http.post(f"/boards/{board_id}/undo").status_code == 409
            assert http.post("/boards/9999/undo").status_code == 404
    finally:
        app.dependency_overrides.clear()


BOARD_PGN = "1. e4 e5 2. Nf3 Nc6 *\n"


@requires_stockfish
async def test_analyzing_a_board_runs_the_same_worker_as_a_game(
    db_session: AsyncSession, db_session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """RF-6.9: la línea principal del tablero se clasifica como una partida.

    Es el mismo worker y la misma tabla `analyzed_moves`: lo único propio es
    que el PGN lo manda el front, porque el árbol lo recorre chess.js.
    """
    _override(db_session)
    app.state.worker = AnalysisWorker(session_factory=db_session_factory)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "A analizar"}).json()["id"]
            queued = http.post(f"/boards/{board_id}/analysis", json={"pgn": BOARD_PGN, "depth": 8})
            assert queued.status_code == 201, queued.text
            assert queued.json()["board_id"] == board_id
            assert queued.json()["game_id"] is None

            analysis_id = queued.json()["id"]
            with http.websocket_connect(f"/ws/analysis/{analysis_id}") as ws:
                while ws.receive_json()["status"] == "running":
                    pass

            detail = http.get(f"/analysis/{analysis_id}").json()
            listed = http.get("/analysis", params={"board_id": board_id}).json()
    finally:
        app.dependency_overrides.clear()

    assert detail["status"] == "done", detail
    assert [move["san"] for move in detail["moves"]] == ["e4", "e5", "Nf3", "Nc6"]
    assert detail["white_accuracy"] is not None
    # Y el tablero sabe encontrarlo sin tener que recordar el id.
    assert [item["id"] for item in listed] == [analysis_id]


async def test_analyzing_an_unknown_board_returns_404(db_session: AsyncSession) -> None:
    _override(db_session)
    try:
        with TestClient(app) as http:
            response = http.post("/boards/9999/analysis", json={"pgn": BOARD_PGN})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


async def _board_with_done_analysis(
    db_session: AsyncSession, *, analyzed_pgn: str = BOARD_PGN
) -> int:
    """Un tablero con una jugada analizada y clasificada, sin pasar por el
    motor: lo que se quiere probar es qué cuenta y qué no, no el análisis."""
    from lucia_api.db.models import Analysis, AnalyzedMove, Board

    board = Board(title="Mía de verdad", root_fen=chess.STARTING_FEN, tree_json=SAMPLE_TREE)
    db_session.add(board)
    await db_session.flush()
    analysis = Analysis(
        board_id=board.id,
        analyzed_pgn=analyzed_pgn,
        engine="stockfish",
        depth=8,
        multipv=1,
        status="done",
    )
    db_session.add(analysis)
    await db_session.flush()
    db_session.add(
        AnalyzedMove(
            analysis_id=analysis.id,
            ply=0,
            color="white",
            san="e4",
            uci="e2e4",
            fen_before=chess.STARTING_FEN,
            classification="blunder",
            phase="opening",
            move_accuracy=10.0,
            win_percent_before=50.0,
            win_percent_after=10.0,
        )
    )
    await db_session.commit()
    return board.id


#: Lo que la pantalla manda al marcar un tablero como partida propia (RF-6.5):
#: los datos que el tablero no tiene, más sus jugadas en PGN.
OWN_GAME_BODY = {
    "player_color": "white",
    "opponent_name": "Rival OTB",
    "result": "loss",
    "played_on": "2026-03-14",
    "username": "jesus",
    "pgn": BOARD_PGN,
}


async def test_a_board_that_is_not_marked_does_not_count_in_the_stats(
    db_session: AsyncSession,
) -> None:
    """RF-6.5 por defecto: un tablero es un sitio para tantear y sus análisis
    no entran en el dashboard. Lo decide `latest_analysis_ids`."""
    from lucia_api.services.stats import get_player_stats

    await _board_with_done_analysis(db_session)

    stats = await get_player_stats(db_session, "jesus")

    assert stats.total_games == 0
    assert stats.analyzed_games == 0
    assert stats.by_mistake_type == []
    assert stats.by_phase == []


async def test_marking_a_board_as_own_game_publishes_it_to_the_history(
    db_session: AsyncSession,
) -> None:
    """RF-6.5: marcado como partida propia, el tablero se publica como una
    partida más y desde ahí cuenta en marcador, aperturas y patrones."""
    from lucia_api.services.stats import get_player_stats

    board_id = await _board_with_done_analysis(db_session)
    _override(db_session)
    try:
        with TestClient(app) as http:
            marked = http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            assert marked.status_code == 200, marked.text
            own_game = marked.json()["own_game"]
            assert marked.json()["is_own_game"] is True
            assert own_game["opponent_name"] == "Rival OTB"

            published = http.get(f"/games/{own_game['game_id']}").json()
            assert published["white_username"] == "jesus"
            assert published["black_username"] == "Rival OTB"
    finally:
        app.dependency_overrides.clear()

    stats = await get_player_stats(db_session, "jesus")

    assert stats.overall.losses == 1
    assert stats.analyzed_games == 1
    assert [phase.phase for phase in stats.by_phase] == ["opening"]
    # La apertura se deduce de las jugadas, como en cualquier partida.
    assert [opening.eco for opening in stats.by_opening] == ["C44"]


async def test_withdrawing_the_mark_takes_the_game_out_of_the_history(
    db_session: AsyncSession,
) -> None:
    """Retirar la marca deja el tablero como estaba y se lleva la partida: el
    historial es lo que el usuario jugó, y él mismo ha dicho que esa no lo
    es."""
    from lucia_api.services.stats import get_player_stats

    board_id = await _board_with_done_analysis(db_session)
    _override(db_session)
    try:
        with TestClient(app) as http:
            http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            withdrawn = http.delete(f"/boards/{board_id}/own-game")
            assert withdrawn.status_code == 200, withdrawn.text
            assert withdrawn.json()["is_own_game"] is False
            assert withdrawn.json()["own_game"] is None
            assert withdrawn.json()["tree_json"] == SAMPLE_TREE  # el tablero sigue entero
    finally:
        app.dependency_overrides.clear()

    assert (await get_player_stats(db_session, "jesus")).total_games == 0


async def test_editing_a_published_board_stops_its_old_analysis_from_counting(
    db_session: AsyncSession,
) -> None:
    """El tablero se sigue editando después de marcarlo. La partida publicada
    sigue a las jugadas, y el análisis deja de contar en cuanto lo analizado
    ya no es lo que hay: pegar la clasificación de una jugada sobre otra sería
    meter un dato falso en el dashboard."""
    from lucia_api.services.stats import get_player_stats

    board_id = await _board_with_done_analysis(db_session)
    edited_pgn = "1. d4 d5 *\n"
    _override(db_session)
    try:
        with TestClient(app) as http:
            http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            edited = http.put(
                f"/boards/{board_id}",
                json={"tree_json": _tree_with("d4"), "pgn": edited_pgn},
            )
            assert edited.status_code == 200, edited.text
    finally:
        app.dependency_overrides.clear()

    stats = await get_player_stats(db_session, "jesus")

    # La partida sigue contando para el marcador, que no depende del análisis.
    assert stats.overall.losses == 1
    # Lo que sale del dashboard es lo que dependía del análisis viejo.
    assert stats.analyzed_games == 0
    assert stats.by_phase == []


async def test_saving_a_published_board_without_its_pgn_is_refused(
    db_session: AsyncSession,
) -> None:
    """Guardar sin decir cómo quedó el tablero dejaría la partida publicada
    atrasada en silencio, que es el fallo que nadie ve."""
    _override(db_session)
    try:
        with TestClient(app) as http:
            board_id = http.post("/boards", json={"title": "Publicado"}).json()["id"]
            http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            response = http.put(f"/boards/{board_id}", json={"tree_json": _tree_with("d4")})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def test_deleting_a_board_takes_its_analyses_and_versions_with_it(
    db_session: AsyncSession,
) -> None:
    """Sin el tablero, sus clasificaciones y sus versiones no describen nada.

    Lo hacen las claves foráneas del esquema (`ON DELETE CASCADE`), que en
    sqlite solo se ejecutan con `PRAGMA foreign_keys=ON`: viene apagado por
    conexión y lo enciende `db/base.py::create_db_engine`. Sin él esto pasaba
    en silencio y la base se iba llenando de filas huérfanas.
    """
    from lucia_api.db.models import Analysis, AnalyzedMove, BoardVersion

    board_id = await _board_with_done_analysis(db_session)
    _override(db_session)
    try:
        with TestClient(app) as http:
            http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            assert http.delete(f"/boards/{board_id}").status_code == 204
    finally:
        app.dependency_overrides.clear()

    async def count(model, condition) -> int:
        return (
            await db_session.execute(select(func.count()).select_from(model).where(condition))
        ).scalar_one()

    assert await count(BoardVersion, BoardVersion.board_id == board_id) == 0
    assert await count(Analysis, Analysis.board_id == board_id) == 0
    # Y las jugadas del análisis se van con él, por la misma regla.
    assert await count(AnalyzedMove, AnalyzedMove.analysis_id.is_not(None)) == 0


async def test_withdrawing_the_mark_keeps_the_board_analysis(db_session: AsyncSession) -> None:
    """Retirar la marca se lleva la partida del historial, no el análisis: las
    jugadas siguen siendo las del tablero y la pantalla las sigue enseñando
    clasificadas. Solo deja de contar en las Estadísticas."""
    from lucia_api.db.models import Analysis

    board_id = await _board_with_done_analysis(db_session)
    _override(db_session)
    try:
        with TestClient(app) as http:
            http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            http.delete(f"/boards/{board_id}/own-game")
    finally:
        app.dependency_overrides.clear()

    remaining = (
        (await db_session.execute(select(Analysis).where(Analysis.board_id == board_id)))
        .scalars()
        .all()
    )
    assert len(remaining) == 1
    assert remaining[0].game_id is None


async def test_undoing_a_published_board_takes_the_game_back_with_it(
    db_session: AsyncSession,
) -> None:
    """Deshacer devuelve también la partida publicada a las jugadas de antes,
    en la misma petición: cada versión del historial guarda su PGN (RF-6.8),
    así que el servidor no tiene que pedírselo a la pantalla."""
    from lucia_api.db.models import Analysis

    board_id = await _board_with_done_analysis(db_session)
    _override(db_session)
    try:
        with TestClient(app) as http:
            # El tablero se arma desde la API para que tenga historial: la
            # primera versión es la que guarda este PGN.
            http.put(f"/boards/{board_id}", json={"tree_json": SAMPLE_TREE, "pgn": BOARD_PGN})
            http.put(f"/boards/{board_id}/own-game", json=OWN_GAME_BODY)
            # Una edición: la partida publicada la sigue y el análisis caduca.
            http.put(
                f"/boards/{board_id}",
                json={"tree_json": _tree_with("d4"), "pgn": "1. d4 *\n"},
            )
            undone = http.post(f"/boards/{board_id}/undo")
            assert undone.status_code == 200, undone.text
            game = http.get(f"/games/{undone.json()['own_game']['game_id']}").json()
    finally:
        app.dependency_overrides.clear()

    # El historial vuelve a enseñar las jugadas de antes de la edición.
    assert "e4" in game["pgn"] and "d4" not in game["pgn"]
    # Y el análisis vuelve a contar, porque es otra vez el de estas jugadas.
    analysis = (
        await db_session.execute(select(Analysis).where(Analysis.board_id == board_id))
    ).scalar_one()
    assert analysis.game_id is not None

/** Una partida de sparring en marcha (RF-4.3): el tablero donde se juega y el
 * panel que dice contra quién, cómo va y cómo acabó.
 *
 * **También las retomadas** (RF-4.4): una partida que empieza a mitad de una
 * propia se juega aquí igual que cualquier otra, y lo único que añade es de
 * dónde salió, con enlace de vuelta al visor. Quien mueve primero es quien
 * tenga el turno en la posición de partida, que puede ser cualquiera de los
 * dos.
 *
 * **El servidor es el rival y también el árbitro.** Aquí no se guarda la
 * partida: se manda la jugada y vuelve el estado entero —posición, jugadas,
 * resultado— con la respuesta del motor ya dentro. Por eso la pantalla no
 * tiene que reconciliar nada, y recargar a mitad de partida la deja donde
 * estaba.
 *
 * Es la diferencia con el tablero de análisis (RF-6), donde quien sabe de
 * reglas es chess.js y la API solo guarda el árbol: allí el servidor custodia
 * un documento, y aquí juega.
 *
 * **Sin barra de evaluación**, como en los puzzles: un rival calibrado se
 * entrena jugando contra él, y una barra diciendo a cada jugada quién va
 * ganando convierte la partida en un análisis asistido. **Con capa de
 * ocupación**, en cambio (RF-7, y lo mismo en las otras dos pantallas de
 * entrenamiento con tablero): esa no es la opinión del motor sobre la
 * posición, es leer la posición que ya está en pantalla — el matiz que decide
 * qué ayuda entra aquí y cuál no.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useMemo } from "react";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner, SuccessBox, WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { BoardFrame } from "../../components/board/BoardFrame";
import { KEYBOARD_MOVE_HINT, OCCUPANCY_TOGGLE_KEY_HINT } from "../../components/board/hints";
import { Chessboard } from "../../components/board/Chessboard";
import { legalMovesByOrigin } from "../../components/board/legalMoves";
import { OccupancyPanel } from "../../components/board/OccupancyPanel";
import { useOccupancy } from "../../components/board/useOccupancy";
import {
  BOARD_HINT_CLASSES,
  BOARD_SIDEBAR_GRID_CLASS,
  MOVE_LIST_HEIGHT_CLASS,
} from "../../components/styles";
import { api } from "../../lib/api";
import { formatBoardTitleFromPgnHeaders, formatOpponentName } from "../../lib/format";
import { moveNumberLabel } from "../../lib/moves";
import { fromPgn } from "../board/tree";
import { outcomeFor, outcomeSentence, turnsOf } from "./sparring";
import { ExerciseStatusBadge } from "./ExerciseStatusBadge";
import { SPARRING_GAMES_QUERY_KEY } from "./SparringPage";

export function SparringGamePage() {
  const { sparringGameId } = useParams({
    from: "/training/sparring/$sparringGameId",
  });
  const gameId = Number(sparringGameId);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const gameQuery = useQuery({
    queryKey: ["sparring", "games", gameId],
    queryFn: () => api.getSparringGame(gameId),
  });
  const game = gameQuery.data;

  /** Jugar y recibir la respuesta del motor es una sola petición, así que
   * mientras está en vuelo el tablero se bloquea: es el turno del rival. */
  const moveMutation = useMutation({
    mutationFn: (uci: string) => api.playSparringMove(gameId, uci),
    onSuccess: (updated) => {
      queryClient.setQueryData(["sparring", "games", gameId], updated);
      queryClient.invalidateQueries({ queryKey: SPARRING_GAMES_QUERY_KEY });
    },
  });

  const resignMutation = useMutation({
    mutationFn: () => api.resignSparringGame(gameId),
    onSuccess: (updated) => {
      queryClient.setQueryData(["sparring", "games", gameId], updated);
      queryClient.invalidateQueries({ queryKey: SPARRING_GAMES_QUERY_KEY });
    },
  });

  /** Abrir como tablero de análisis (RF-6.6), que es como se analiza una
   * partida de sparring: el tablero tiene su análisis completo (RF-6.9) y no
   * entra en las estadísticas mientras no se publique (RF-6.5), que es justo
   * lo que corresponde a una partida contra un motor mutilado. */
  const openAsBoardMutation = useMutation({
    mutationFn: async () => {
      const parsed = fromPgn(game!.pgn); // lanza con el motivo si no hay jugadas
      return api.createBoard({
        title: formatBoardTitleFromPgnHeaders(parsed.headers) ?? "Sparring",
        root_fen: parsed.root.fen,
        tree_json: parsed.root,
      });
    },
    onSuccess: (board) =>
      navigate({
        to: "/boards/$boardId",
        params: { boardId: String(board.id) },
      }),
  });

  const isEngineThinking = moveMutation.isPending;
  const canMove = game?.is_player_turn === true && !isEngineThinking;
  const legalMoves = useMemo(
    () => (game && canMove ? legalMovesByOrigin(game.fen) : undefined),
    [game, canMove],
  );
  /** La capa de ocupación (RF-7) sobre la posición en juego. Va antes de los
   * retornos tempranos porque es un hook, y mientras la partida se carga
   * recibe un FEN vacío del que `computeOccupancy` ya devuelve `null`. Las
   * marcas arrancan apagadas: las colgadas de RF-7.4 durante una partida en
   * marcha son el aviso de blunder que un rival calibrado no debe dar. */
  const occupancyController = useOccupancy(game?.fen ?? "", {
    marksOnByDefault: false,
  });

  function tryMove(from: string, to: string) {
    if (!game || !canMove) return;
    const chess = new Chess(game.fen);
    try {
      // La promoción siempre a dama, igual que en el tablero de análisis y en
      // los puzzles.
      const move = chess.move({ from, to, promotion: "q" });
      moveMutation.mutate(move.lan);
    } catch {
      // jugada ilegal; chessground ya filtra casi todas
    }
  }

  if (gameQuery.isPending) return <Spinner label="Cargando la partida…" />;
  if (gameQuery.isError) {
    return <ErrorBox error={gameQuery.error} onRetry={gameQuery.refetch} />;
  }
  if (!game) return null;

  const playerColor = game.player_color === "black" ? "black" : "white";
  /** El nombre del rival se compone aquí, como en el formulario que abrió la
   * partida y en el listado: es el mismo formateador para los tres (fila 96
   * del inventario). */
  const opponentName = formatOpponentName(game.engine, game.engine_elo);
  const outcome = outcomeFor(game);
  const turns = turnsOf(game.moves_san, game.starting_ply);

  return (
    <div className="space-y-6">
      {/* Una partida concreta es una pantalla de detalle, y se encabeza como
          las otras dos que lo son —el visor y el tablero de análisis—: el
          enlace de vuelta sobre un título que nombra lo que se tiene delante.
          Llevaba la cabecera de la sección (`TrainingHeader`), así que se
          titulaba "Entrenamiento", volvía atrás con un botón al final del
          lateral y la pestaña "Sparring" hacía lo mismo con otro nombre —dos
          controles para una sola cosa— (fila 94 del inventario de
          docs/07-coherencia-ui.md, criterio C-2). */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/training/sparring" className="text-sm opacity-70 hover:underline">
            ← Volver a sparring
          </Link>
          <h1 className="mt-1 text-2xl font-bold">Partida contra {opponentName}</h1>
          <p className="mt-1 text-sm opacity-70">No cuenta en tus estadísticas.</p>
        </div>

        {/* La acción de la partida va en la cabecera y no al final del lateral,
            que es donde la ponen las otras dos pantallas de detalle: desde que
            esta se encabeza como ellas (fila 94), "Abrir como tablero" se
            llamaba igual que allí y vivía en otro sitio (fila 109, criterio
            C-2). Solo hay una a la vez, porque abandonar y llevarse la partida
            al tablero son de dos momentos distintos. */}
        <div className="flex flex-wrap items-center gap-2">
          {outcome === null ? (
            <Button
              variant="danger"
              disabled={resignMutation.isPending || isEngineThinking}
              // Pregunta antes, como eliminar un tablero, borrar una variante o
              // quitar la marca de partida propia: abandonar termina la partida
              // y no hay deshacer (criterio C-2, la misma regla que cerró la
              // fila 87).
              onClick={() => {
                const question =
                  "¿Abandonar la partida? Cuenta como derrota y no se puede deshacer.";
                if (window.confirm(question)) resignMutation.mutate();
              }}
            >
              {resignMutation.isPending ? "Abandonando…" : "Abandonar"}
            </Button>
          ) : (
            <Button
              variant="primary"
              disabled={openAsBoardMutation.isPending}
              onClick={() => openAsBoardMutation.mutate()}
            >
              {/* Mismo nombre que en el visor, que es la otra pantalla desde la
                  que se lleva una partida al tablero (C-2). */}
              {openAsBoardMutation.isPending ? "Abriendo…" : "Abrir como tablero"}
            </Button>
          )}
        </div>
      </div>

      {/* Qué hace la acción, a la vista y no en un `title`, con la misma forma y
          en el mismo sitio que en el visor (fila 103, criterios C-6 y C-7). */}
      <p className="text-xs opacity-60">
        {outcome === null
          ? "Abandonar cuenta como derrota y no se puede deshacer."
          : "«Abrir como tablero» crea un tablero de análisis con las jugadas de esta partida. Allí se puede analizar entera; la partida de sparring se queda como está."}
      </p>

      {/* El fallo de cada acción, junto a la acción: en el lateral quedaba a
          dos columnas del botón que lo provocó (criterio C-3). */}
      {resignMutation.isError && <ErrorBox error={resignMutation.error} />}
      {openAsBoardMutation.isError && <ErrorBox error={openAsBoardMutation.error} />}

      <div className={BOARD_SIDEBAR_GRID_CLASS}>
        <div className="space-y-3">
          <BoardFrame>
            <Chessboard
              fen={game.fen}
              orientation={playerColor}
              turnColor={playerColor}
              legalMoves={legalMoves}
              onMove={tryMove}
              lastMoveUci={game.last_move_uci}
              occupancyController={occupancyController}
            />
          </BoardFrame>
          {/* Lo que hay que saber del tablero, en la misma frase y en el mismo
              sitio que en el visor, el tablero de análisis y los puzzles
              (criterio C-1). */}
          <p className={BOARD_HINT_CLASSES}>
            {outcome !== null
              ? "La partida terminó: el tablero ya no se mueve."
              : "Arrastra una pieza para jugar. Las promociones se coronan en dama."}{" "}
            {OCCUPANCY_TOGGLE_KEY_HINT}
            {/* El teclado se anuncia donde se anuncia el arrastre y no más,
                igual que en el puzzle y en el drill: con la partida terminada
                el tablero no acepta jugadas por ninguna de las dos vías
                (criterio C-1). Mientras el motor piensa sí se sigue anunciando,
                como el arrastre: es una espera de un segundo, no un estado de
                la pantalla. */}
            {outcome === null ? ` ${KEYBOARD_MOVE_HINT}` : ""}
          </p>

          <OccupancyPanel controller={occupancyController} />
        </div>

        <aside className="space-y-3">
          <Panel
            title={`Juegas con ${playerColor === "white" ? "blancas" : "negras"}`}
            aside={
              <ExerciseStatusBadge
                isPlayerTurn={game.is_player_turn}
                isWaitingForServer={isEngineThinking}
                waitingLabel="el motor piensa…"
                finishedLabel="partida terminada"
              />
            }
          >
            <p className="text-sm">Rival: {opponentName}</p>
            <p className="mt-1 text-xs opacity-70">
              {game.engine === "stockfish"
                ? "Stockfish jugando al Elo que le pediste: juega bien y se contiene."
                : "Lc0 con una red Maia: imita a una persona de ~1500, con sus errores."}
            </p>
            {/* De dónde salió, cuando se retomó una partida propia (RF-4.4):
                sin esto, una partida que empieza a mitad no dice por qué
                empieza ahí. El número sale de `starting_ply` —el ply real de
                la posición desde la que se juega— y no de `origin_ply`, que es
                relativo al inicio de la partida de origen y daría otro número
                si esa no empezaba en la salida. Es el mismo con el que numera
                la lista de jugadas de aquí al lado (criterio C-5). */}
            {game.origin_game_id !== null && game.origin_ply !== null && (
              <p className="mt-2 text-xs opacity-70">
                Retomada desde la jugada {moveNumberLabel(game.starting_ply)} de{" "}
                <Link
                  to="/games/$gameId"
                  params={{ gameId: String(game.origin_game_id) }}
                  className="underline"
                >
                  una partida tuya
                </Link>
                .
              </p>
            )}
          </Panel>

          {moveMutation.isError && <ErrorBox error={moveMutation.error} />}

          {outcome !== null &&
            (outcome === "win" ? (
              <SuccessBox>{outcomeSentence(game)}.</SuccessBox>
            ) : (
              <WarningBox>{outcomeSentence(game)}.</WarningBox>
            ))}

          <Panel title="Jugadas" bodyClassName="">
            {turns.length === 0 ? (
              /* El vacío es el compartido y no una frase suelta (criterio
                 C-4), con el mismo envoltorio que el del lateral del visor:
                 el cuerpo del panel no lleva relleno porque lo gestiona la
                 lista. */
              <div className="p-3">
                <EmptyState title="Todavía no se ha jugado nada" />
              </div>
            ) : (
              <ol className={`${MOVE_LIST_HEIGHT_CLASS} overflow-y-auto text-sm`}>
                {turns.map((turn) => (
                  <li
                    key={turn.number}
                    className="grid grid-cols-[2.5rem_1fr_1fr] gap-1 border-b border-slate-100 px-1 py-0.5 dark:border-slate-800"
                  >
                    <span className="tabular-nums opacity-50">{turn.number}.</span>
                    <span>{turn.white}</span>
                    <span>{turn.black}</span>
                  </li>
                ))}
              </ol>
            )}
          </Panel>
        </aside>
      </div>
    </div>
  );
}

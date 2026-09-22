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
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner, SuccessBox, WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { Chessboard } from "../../components/board/Chessboard";
import { legalMovesByOrigin } from "../../components/board/legalMoves";
import { OccupancyPanel } from "../../components/board/OccupancyPanel";
import { OCCUPANCY_TOGGLE_KEY_HINT, useOccupancy } from "../../components/board/useOccupancy";
import {
  BOARD_HINT_CLASSES,
  BOARD_SIDEBAR_GRID_CLASS,
  buttonClasses,
  MOVE_LIST_HEIGHT_CLASS,
} from "../../components/styles";
import { api } from "../../lib/api";
import { formatBoardTitleFromPgnHeaders } from "../../lib/format";
import { moveNumberLabel } from "../../lib/moves";
import { fromPgn } from "../board/tree";
import { outcomeFor, outcomeSentence, turnsOf } from "./sparring";
import { SPARRING_GAMES_QUERY_KEY } from "./SparringPage";
import { TrainingHeader } from "./TrainingHeader";

export function SparringGamePage() {
  const { sparringGameId } = useParams({ from: "/training/sparring/$sparringGameId" });
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
      navigate({ to: "/boards/$boardId", params: { boardId: String(board.id) } }),
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
  const occupancyController = useOccupancy(game?.fen ?? "", { marksOnByDefault: false });

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
  const outcome = outcomeFor(game);
  const turns = turnsOf(game.moves_san);

  return (
    <div className="space-y-6">
      <TrainingHeader>
        Partida contra {game.opponent_name}. No cuenta en tus estadísticas.
      </TrainingHeader>

      <div className={BOARD_SIDEBAR_GRID_CLASS}>
        <div className="space-y-3">
          <Chessboard
            fen={game.fen}
            orientation={playerColor}
            turnColor={playerColor}
            legalMoves={legalMoves}
            onMove={tryMove}
            lastMoveUci={game.last_move_uci}
            occupancyController={occupancyController}
          />
          {/* Lo que hay que saber del tablero, en la misma frase y en el mismo
              sitio que en el visor, el tablero de análisis y los puzzles
              (criterio C-1). */}
          <p className={BOARD_HINT_CLASSES}>
            {outcome !== null
              ? "La partida terminó: el tablero ya no se mueve."
              : "Arrastra una pieza para jugar. Las promociones se coronan en dama."}{" "}
            {OCCUPANCY_TOGGLE_KEY_HINT}
          </p>

          <OccupancyPanel controller={occupancyController} />
        </div>

        <aside className="space-y-3">
          <Panel
            title={`Juegas con ${playerColor === "white" ? "blancas" : "negras"}`}
            aside={<TurnBadge isPlayerTurn={game.is_player_turn} isThinking={isEngineThinking} />}
          >
            <p className="text-sm">Rival: {game.opponent_name}</p>
            <p className="mt-1 text-xs opacity-70">
              {game.engine === "stockfish"
                ? "Stockfish jugando al Elo que le pediste: juega bien y se contiene."
                : "Lc0 con una red Maia: imita a una persona de ~1500, con sus errores."}
            </p>
            {/* De dónde salió, cuando se retomó una partida propia (RF-4.4):
                sin esto, una partida que empieza a mitad no dice por qué
                empieza ahí. El número se saca del `origin_ply`, que es
                relativo al inicio de la partida de origen: si esa empezaba en
                una posición dada, el visor la numera desde su jugada real y
                aquí sale otro número (fila 101 del inventario, criterio
                C-5). */}
            {game.origin_game_id !== null && game.origin_ply !== null && (
              <p className="mt-2 text-xs opacity-70">
                Retomada desde la jugada {moveNumberLabel(game.origin_ply)} de{" "}
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
          {resignMutation.isError && <ErrorBox error={resignMutation.error} />}
          {openAsBoardMutation.isError && <ErrorBox error={openAsBoardMutation.error} />}

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

          <div className="flex flex-wrap gap-2">
            {outcome === null ? (
              <Button
                variant="danger"
                disabled={resignMutation.isPending || isEngineThinking}
                // Pregunta antes, como eliminar un tablero, borrar una variante
                // o quitar la marca de partida propia: abandonar termina la
                // partida y no hay deshacer (criterio C-2, la misma regla que
                // cerró la fila 87).
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
                // Qué se lleva el tablero, con la misma forma y casi las mismas
                // palabras que el "Abrir como tablero" del visor (criterio
                // C-6): sin esto la diferencia se descubre al llegar.
                title="Crea un tablero de análisis con las jugadas de esta partida. Allí se puede analizar entera; la partida de sparring se queda como está."
                onClick={() => openAsBoardMutation.mutate()}
              >
                {/* Mismo nombre que en el visor, que es la otra pantalla desde
                    la que se lleva una partida al tablero (criterio C-2). */}
                {openAsBoardMutation.isPending ? "Abriendo…" : "Abrir como tablero"}
              </Button>
            )}
            <Link to="/training/sparring" className={buttonClasses()}>
              Volver a Sparring
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}

/** De quién es el turno, dicho arriba del panel y no solo por si el tablero
 * deja mover: "el motor está pensando" es un estado del sistema y tiene que
 * verse (criterio C-3). */
function TurnBadge({
  isPlayerTurn,
  isThinking,
}: {
  isPlayerTurn: boolean;
  isThinking: boolean;
}) {
  if (isThinking) return <Badge tone="info">el motor piensa…</Badge>;
  if (isPlayerTurn) return <Badge tone="success">te toca</Badge>;
  return <Badge tone="neutral">terminada</Badge>;
}

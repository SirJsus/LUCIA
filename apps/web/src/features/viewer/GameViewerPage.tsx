/** Visor de una partida (RF-5.1): tablero, jugadas clasificadas, gráfico de
 * evaluación y disparo del análisis con progreso en vivo.
 *
 * Desde aquí también se abre la partida como tablero de análisis (RF-6.6):
 * una copia desacoplada donde probar variantes sin tocar ni la partida ni su
 * análisis, que es lo que RF-5.2 pide poder hacer desde el visor. */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "@tanstack/react-router";
import { Chess, DEFAULT_POSITION } from "chess.js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/Button";
import { EngineSelect } from "../../components/EngineSelect";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { CustomPositionBadge } from "../../components/CustomPositionBadge";
import { GameSourceBadge } from "../../components/GameSourceBadge";
import { OCCUPANCY_TOGGLE_KEY_HINT } from "../../components/board/hints";
import { BoardWithEvalBar } from "../../components/board/BoardWithEvalBar";
import { EngineLineList } from "../../components/board/EngineLineList";
import { arrowsFromEngineLines, arrowsFromPreviewLine } from "../../components/board/boardConfig";
import { MoveButton } from "../../components/board/MoveButton";
import { MoveNavigator } from "../../components/board/MoveNavigator";
import { OccupancyPanel } from "../../components/board/OccupancyPanel";
import { useMoveNavigationKeys } from "../../components/board/useMoveNavigationKeys";
import { useOccupancy } from "../../components/board/useOccupancy";
import { EmptyState, ErrorBox, ProgressBox, Spinner } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import {
  BOARD_HINT_CLASSES,
  BOARD_SIDEBAR_GRID_CLASS,
  MOVE_LIST_HEIGHT_CLASS,
} from "../../components/styles";
import { api } from "../../lib/api";
import { saveTextAsFile } from "../../lib/download";
import { classificationStyle, MISTAKE_CLASSIFICATIONS } from "../../lib/classification";
import {
  formatAccuracy,
  formatDate,
  formatDuration,
  formatEngineName,
  formatBoardTitleFromGame,
  formatRating,
  formatTimeClass,
  gameResult,
  type EngineId,
} from "../../lib/format";
import { moveNumberLabel, plyFromFen } from "../../lib/moves";
import { SparringSetupForm, type SparringSetup } from "../training/SparringSetupForm";
import { fromPgn } from "../board/tree";
import { whiteWinPercentAfterMove } from "../../lib/score";
import { CriticalMoments } from "./CriticalMoments";
import { EngineComparison } from "./EngineComparison";
import { EvalChart } from "./EvalChart";
import { MoveList } from "./MoveList";
import { useElapsedSeconds, useTrackedAnalysis } from "../../lib/useTrackedAnalysis";

interface ParsedPosition {
  /** FEN resultante tras esta jugada. */
  fen: string;
  /** Jugada en formato largo ("e2e4"), para resaltarla en el tablero. */
  lan: string;
  san: string;
}

interface ParsedGame {
  /** Posición de partida: la del PGN, que no siempre es la estándar. */
  startingFen: string;
  positions: ParsedPosition[];
}

export function GameViewerPage() {
  const { gameId } = useParams({ from: "/games/$gameId" });
  const id = Number(gameId);
  const navigate = useNavigate();

  const [currentPly, setCurrentPly] = useState(-1); // -1 = posición inicial
  const [analysisId, setAnalysisId] = useState<number | null>(null);
  const [orientation, setOrientation] = useState<"white" | "black">("white");
  const [engine, setEngine] = useState<EngineId>("stockfish");
  const [previewPvUci, setPreviewPvUci] = useState<string[] | null>(null);

  const gameQuery = useQuery({
    queryKey: ["game", id],
    queryFn: () => api.getGame(id),
  });

  // Si la partida ya se analizó antes, se reutiliza en vez de volver a
  // gastar minutos de motor.
  const existingQuery = useQuery({
    queryKey: ["analyses", id],
    queryFn: () => api.listAnalyses({ gameId: id }),
  });

  useEffect(() => {
    const done = existingQuery.data?.find((a) => a.status === "done");
    const pending = existingQuery.data?.find(
      (a) => a.status === "queued" || a.status === "running",
    );
    if (analysisId === null && (done || pending)) setAnalysisId((done ?? pending)!.id);
  }, [existingQuery.data, analysisId]);

  const { analysis, isRunning, progress } = useTrackedAnalysis(analysisId);
  const elapsedSeconds = useElapsedSeconds(isRunning);

  const analyzeMutation = useMutation({
    mutationFn: () => api.createAnalysis({ game_ids: [id], engine }),
    onSuccess: (created) => {
      setAnalysisId(created[0].id);
      void existingQuery.refetch(); // para que aparezca en el selector de motor
    },
  });

  // --- Exportar el PGN anotado (RF-5.5) ---
  // Se pide el archivo, se comprueba la respuesta y solo entonces se guarda.
  // Es lo que permite que un análisis borrado desde otra pestaña acabe en un
  // `ErrorBox` y no en un archivo con el error dentro (fila 70 del inventario
  // de docs/07-coherencia-ui.md).
  const exportPgnMutation = useMutation({
    mutationFn: async (doneAnalysisId: number) => {
      const { text, filename } = await api.getAnalysisPgn(doneAnalysisId);
      saveTextAsFile(filename, text, "application/x-chess-pgn");
    },
  });

  // --- Abrir como tablero de análisis (RF-6.6) ---
  // La copia es **desacoplada**: se lee el PGN una vez y lo que se juegue
  // después en el tablero no vuelve a esta partida ni a su análisis. Se
  // prefiere el PGN anotado (RF-5.5) cuando hay análisis terminado, porque
  // trae los comentarios y las líneas del motor y así el tablero se abre con
  // lo que ya se sabía en vez de con las jugadas peladas.
  const openAsBoardMutation = useMutation({
    mutationFn: async () => {
      const pgn =
        analysis?.status === "done"
          ? (await api.getAnalysisPgn(analysis.id)).text
          : (gameQuery.data?.pgn ?? "");
      const parsed = fromPgn(pgn); // lanza con el motivo si no hay árbol que sacar
      return api.createBoard({
        title: formatBoardTitleFromGame(gameQuery.data!),
        root_fen: parsed.root.fen,
        tree_json: parsed.root,
        // La copia nace sin marcar como "partida propia" (RF-6.5), que es
        // como nace cualquier tablero: la original ya cuenta en las
        // estadísticas, y publicar la copia la contaría dos veces.
      });
    },
    onSuccess: (board) =>
      navigate({
        to: "/boards/$boardId",
        params: { boardId: String(board.id) },
      }),
  });

  // --- Jugar desde aquí contra el motor (RF-4.4) ---
  // La otra puerta de "re-juega desde el error", además de la lista curada de
  // `features/training/ReplaysPage`: desde aquí se retoma **cualquier**
  // posición de la partida, no solo los errores graves.
  // Se retoma la que hay **en pantalla**, y por eso se manda `currentPly + 1`:
  // el ply de la API cuenta jugadas ya hechas y el del visor es el índice de
  // la última jugada hecha. Se manda la partida y la jugada, no el FEN: la
  // posición la deriva el servidor de lo que ya tiene guardado, que es lo que
  // mantiene esto del lado de RF-4.4 y no de RF-11.1 (ver
  // `routers/sparring.py::GamePositionIn` y ADR-0020).
  const [isReplayFormOpen, setReplayFormOpen] = useState(false);
  const startReplayMutation = useMutation({
    mutationFn: (setup: SparringSetup) =>
      api.startSparringGame({
        ...setup,
        origin: { game_id: id, ply: currentPly + 1 },
      }),
    onSuccess: (sparringGame) =>
      navigate({
        to: "/training/sparring/$sparringGameId",
        params: { sparringGameId: String(sparringGame.id) },
      }),
  });

  // Con análisis terminados de dos motores distintos se puede comparar (RF-2.6).
  const doneAnalyses = (existingQuery.data ?? []).filter((a) => a.status === "done");
  const doneAnalysisByEngine = new Map(doneAnalyses.map((a) => [a.engine, a]));
  const canCompareEngines = doneAnalysisByEngine.size >= 2;

  const comparisonQuery = useQuery({
    queryKey: ["comparison", [...doneAnalysisByEngine.values()].map((a) => a.id).sort()],
    queryFn: () => {
      const [a, b] = [...doneAnalysisByEngine.values()];
      return api.compareAnalyses(a.id, b.id);
    },
    enabled: canCompareEngines,
  });

  const { startingFen, positions } = useMemo(
    () => parsePgn(gameQuery.data?.pgn),
    [gameQuery.data?.pgn],
  );

  const currentFen = currentPly < 0 ? startingFen : positions[currentPly].fen;

  // La capa de ocupación (RF-7) se calcula sobre la posición que se está
  // viendo, igual que en el tablero de análisis.
  const occupancyController = useOccupancy(currentFen);

  // Una partida que empieza en la jugada 12 (odds chess, Chess960, partidas
  // desde posición) tiene que numerarse desde ahí en todas partes: lista,
  // gráfico y comparación de motores (criterio C-5).
  const startingPly = useMemo(() => plyFromFen(startingFen), [startingFen]);

  const goTo = useCallback(
    (ply: number) => setCurrentPly(Math.max(-1, Math.min(ply, positions.length - 1))),
    [positions.length],
  );

  // Los cuatro saltos por la partida (RF-5.1), que comparten los botones y el
  // teclado, aquí y en el tablero de análisis.
  const goToStart = useCallback(() => goTo(-1), [goTo]);
  const goToPrevious = useCallback(() => goTo(currentPly - 1), [goTo, currentPly]);
  const goToNext = useCallback(() => goTo(currentPly + 1), [goTo, currentPly]);
  const goToEnd = useCallback(() => goTo(positions.length - 1), [goTo, positions.length]);
  useMoveNavigationKeys({
    onFirst: goToStart,
    onPrevious: goToPrevious,
    onNext: goToNext,
    onLast: goToEnd,
  });

  // Lo que el motor proponía en la posición que se está viendo: son las
  // alternativas guardadas con la jugada **siguiente**, porque están tomadas
  // desde la posición anterior a ella (RF-10.1).
  const nextAnalyzedMove = analysis?.moves[currentPly + 1];

  // Las mismas flechas que el tablero de análisis (RF-10.2), con la línea que
  // se esté señalando por encima de ellas. Un análisis anterior a RF-10 cuyas
  // posiciones ya no estén en la caché no tiene alternativas: entonces se
  // dibuja la única flecha que sí se guardó.
  const engineArrows = useMemo(() => {
    if (previewPvUci) return arrowsFromPreviewLine(previewPvUci);
    const alternativeArrows = arrowsFromEngineLines(nextAnalyzedMove?.alternatives);
    if (alternativeArrows.length > 0) return alternativeArrows;
    const bestMoveUci = nextAnalyzedMove?.best_move_uci;
    return bestMoveUci ? [{ uci: bestMoveUci, brush: "green" as const }] : [];
  }, [previewPvUci, nextAnalyzedMove]);

  // Al cambiar de jugada, la línea señalada era continuación de otra posición.
  useEffect(() => setPreviewPvUci(null), [currentPly]);

  // En la posición inicial nadie ha movido todavía: 50-50 mientras haya
  // análisis, y sin barra si no lo hay.
  const currentAnalyzedMove = currentPly >= 0 ? analysis?.moves[currentPly] : undefined;

  // Las alternativas del panel son las de la posición que se está viendo, las
  // mismas que dibujan las flechas: si fueran las de la jugada anterior —que
  // es donde se guardan las de "en su lugar"— señalar una línea dibujaría una
  // continuación media jugada por detrás, sobre piezas que ya se movieron.
  //
  // Con eso, "lo que podías haber jugado en su lugar" (RF-10.2) es esta misma
  // lista mirada desde aquí: `nextAnalyzedMove` es la jugada que se hizo desde
  // esta posición, así que cuando salió mal el panel lo dice y marca en la
  // lista cuál fue.
  const positionAlternatives = nextAnalyzedMove?.alternatives ?? [];
  const wasNextMoveAMistake =
    nextAnalyzedMove !== undefined &&
    MISTAKE_CLASSIFICATIONS.includes(nextAnalyzedMove.classification);
  const whiteWinPercent = currentAnalyzedMove
    ? whiteWinPercentAfterMove(currentAnalyzedMove)
    : analysis?.status === "done"
      ? 50
      : null;

  if (gameQuery.isPending) return <Spinner label="Cargando la partida…" />;
  if (gameQuery.isError) return <ErrorBox error={gameQuery.error} onRetry={gameQuery.refetch} />;

  const game = gameQuery.data;
  const lastMoveUci = currentPly < 0 ? null : positions[currentPly].lan;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/" className="text-sm opacity-70 hover:underline">
            ← Volver a partidas
          </Link>
          <h1 className="mt-1 text-2xl font-bold">
            {game.white_username}{" "}
            <span className="opacity-60">({formatRating(game.white_rating)})</span>{" "}
            <span className="font-mono">{gameResult(game)}</span> {game.black_username}{" "}
            <span className="opacity-60">({formatRating(game.black_rating)})</span>
          </h1>
          <p className="flex flex-wrap items-center gap-2 text-sm opacity-60">
            <span>
              {formatDate(game.played_at)} · {formatTimeClass(game.time_class)} ·{" "}
              {game.rated ? "puntuada" : "amistosa"}
            </span>
            {/* De dónde vino la partida y si empieza en una posición dada: las
                dos explican huecos o rarezas que sin una palabra se leen como
                un fallo de la aplicación. Mismas insignias y mismo orden que en
                el listado (criterio C-2). */}
            <GameSourceBadge platform={game.platform} />
            {game.starts_from_custom_position && <CustomPositionBadge />}
          </p>
        </div>

        {/* Mismo orden que la cabecera del tablero de análisis —girar ·
            motor · las acciones que sacan la partida de aquí · la principal—
            para no tener que buscar los controles al cambiar de pantalla
            (criterio C-2 de docs/07-coherencia-ui.md). `flex-wrap` porque en
            una ventana estrecha se desbordan. */}
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => setOrientation(orientation === "white" ? "black" : "white")}>
            Girar tablero
          </Button>
          <EngineSelect value={engine} onChange={setEngine} />
          {/* Está **siempre**, también sin análisis: deshabilitado y diciendo
              qué falta para que sirva. Antes no existía hasta que había un
              análisis terminado, así que quien abría una partida sin analizar
              no podía saber que la exportación existe ni que analizar es lo
              que la trae. Es lo que ya hace la barra de filtros de Partidas
              con sus tres campos (fila 68 del inventario, criterio C-3).

              Y es un botón, no un `<a download>`: con el enlace la descarga la
              hacía el navegador, y un 409 o un 404 se guardaban como si fueran
              el archivo sin que la pantalla dijera nada (fila 70). Ahora el
              error sale en su `ErrorBox`, como el del resto de acciones. */}
          <Button
            onClick={() => analysis && exportPgnMutation.mutate(analysis.id)}
            disabled={analysis?.status !== "done" || exportPgnMutation.isPending}
          >
            {exportPgnMutation.isPending ? "Exportando…" : "Exportar PGN anotado"}
          </Button>
          {/* Va junto a "Exportar PGN anotado" porque las dos sacan la partida
              de aquí: una a un archivo y otra a un tablero propio. A
              diferencia de aquella, esta no necesita análisis: una partida sin
              analizar también se puede explorar (criterio C-3). */}
          <Button
            onClick={() => openAsBoardMutation.mutate()}
            disabled={openAsBoardMutation.isPending}
          >
            {openAsBoardMutation.isPending ? "Abriendo…" : "Abrir como tablero"}
          </Button>
          {/* Junto a "Abrir como tablero" porque las dos se llevan la partida
              de aquí a otra pantalla; esta se lleva solo la posición, para
              seguir jugándola contra el motor. Tampoco necesita análisis: se
              puede retomar cualquier posición (criterio C-3). */}
          <Button
            onClick={() => setReplayFormOpen(!isReplayFormOpen)}
            disabled={startReplayMutation.isPending}
          >
            {isReplayFormOpen ? "Cancelar" : "Jugar desde aquí"}
          </Button>
          <Button
            variant="primary"
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending || isRunning}
          >
            {isRunning || analyzeMutation.isPending
              ? "Analizando…"
              : doneAnalysisByEngine.has(engine)
                ? `Reanalizar con ${formatEngineName(engine)}`
                : `Analizar con ${formatEngineName(engine)}`}
          </Button>
        </div>
      </div>

      {/* Qué hacen las tres acciones que sacan la partida de aquí, a la vista y
          no en un `title`: con teclado un `title` no aparece nunca, y en un
          botón deshabilitado —que es como está "Exportar PGN anotado" sin
          análisis— tampoco. Es la misma forma con la que Puzzles y Aperturas
          explican su botón de generar, y lo que cerraron las filas 56 y 57 en
          la barra de filtros de Partidas y en la goma del editor de posición
          (fila 103 del inventario, criterios C-6 y C-7). */}
      <p className="text-xs opacity-60">
        <strong className="font-medium">Exportar PGN anotado</strong> descarga la partida con los
        comentarios del análisis y sus variantes, para abrirla en lichess o ChessBase
        {analysis?.status === "done" ? "" : "; hay que analizarla antes"}.{" "}
        <strong className="font-medium">Abrir como tablero</strong> crea un tablero de análisis con
        sus jugadas
        {analysis?.status === "done"
          ? " y los comentarios del análisis"
          : "; analízala antes si quieres llevarte también los comentarios"}
        . <strong className="font-medium">Jugar desde aquí</strong> abre una partida contra el motor
        desde la posición que estás viendo. Ninguna de las tres toca esta partida ni su análisis.
      </p>

      {isReplayFormOpen && (
        <Panel title={`Jugar desde la jugada ${moveNumberLabel(currentPly + startingPly + 1)}`}>
          {/* El bando que se ofrece es el que tiene el turno en esa posición,
              que es lo que se viene a hacer: seguir desde ahí. Se puede
              cambiar, y entonces abre el motor.

              El botón dice "Retomar la partida", igual que en la lista de
              re-jugar: es la misma acción desde otra pantalla (criterio C-2).
              "Empezar partida" es la de Sparring, que es otra cosa —una
              partida desde cero— y por eso conserva su nombre. */}
          <SparringSetupForm
            defaultPlayerColor={plyFromFen(currentFen) % 2 === 0 ? "white" : "black"}
            submitLabel="Retomar la partida"
            pendingLabel="Abriendo partida…"
            isPending={startReplayMutation.isPending}
            onSubmit={(setup) => startReplayMutation.mutate(setup)}
          />
        </Panel>
      )}

      {startReplayMutation.isError && <ErrorBox error={startReplayMutation.error} />}
      {analyzeMutation.isError && <ErrorBox error={analyzeMutation.error} />}
      {exportPgnMutation.isError && <ErrorBox error={exportPgnMutation.error} />}
      {openAsBoardMutation.isError && <ErrorBox error={openAsBoardMutation.error} />}
      {existingQuery.isError && (
        <ErrorBox error={existingQuery.error} onRetry={existingQuery.refetch} />
      )}
      {analysis?.status === "error" && (
        <ErrorBox error={new Error(analysis.error ?? "el análisis falló")} />
      )}

      {/* El mismo trabajo corre desde el tablero de análisis (RF-6.9) y allí
          el recuadro dice con qué motor: es el mismo estado y se anuncia con
          las mismas palabras en los dos sitios (criterio C-2). */}
      {isRunning && analysis && (
        <ProgressBox
          label={`Analizando con ${formatEngineName(analysis.engine)}…`}
          detail={`${
            progress ? `posición ${progress.ply} de ${progress.total}` : "en cola"
          } · ${formatDuration(elapsedSeconds)}`}
          // Sin evento de progreso todavía, el trabajo está encolado: la barra
          // se muestra indeterminada en vez de fingir un 0 %.
          progress={progress ? (progress.ply / progress.total) * 100 : null}
        />
      )}

      <div className={BOARD_SIDEBAR_GRID_CLASS}>
        <div className="space-y-3">
          <BoardWithEvalBar
            fen={currentFen}
            orientation={orientation}
            lastMoveUci={lastMoveUci}
            engineArrows={engineArrows}
            whiteWinPercent={whiteWinPercent}
            occupancyController={occupancyController}
          />

          <MoveNavigator
            onFirst={goToStart}
            onPrevious={goToPrevious}
            onNext={goToNext}
            onLast={goToEnd}
            canGoBack={currentPly > -1}
            canGoForward={currentPly < positions.length - 1}
            position={`${currentPly + 1} / ${positions.length}`}
          />

          <p className={BOARD_HINT_CLASSES}>
            ← → recorren la partida, Inicio y Fin van a sus extremos. Pulsa una jugada de la lista o
            del gráfico para saltar a esa posición. Señala una jugada de las alternativas para verla
            sobre el tablero. {OCCUPANCY_TOGGLE_KEY_HINT}
          </p>

          <OccupancyPanel controller={occupancyController} />

          {analysis?.status === "done" && analysis.moves.length > 0 && (
            <EvalChart
              moves={analysis.moves}
              currentPly={currentPly}
              startingPly={startingPly}
              onSelectPly={goTo}
            />
          )}
        </div>

        <aside className="space-y-3">
          {analysis?.status === "done" && (
            <Panel title="Precisión" bodyClassName="p-3 text-sm">
              <div className="flex justify-between">
                <span>{game.white_username}</span>
                <span className="tabular-nums">{formatAccuracy(analysis.white_accuracy)}</span>
              </div>
              <div className="flex justify-between">
                <span>{game.black_username}</span>
                <span className="tabular-nums">{formatAccuracy(analysis.black_accuracy)}</span>
              </div>
              <p className="mt-2 text-xs opacity-60">
                {formatEngineName(analysis.engine)} · profundidad {analysis.depth} ·{" "}
                {analysis.multipv} líneas por posición (MultiPV)
              </p>
            </Panel>
          )}

          {analysis?.status === "done" && nextAnalyzedMove !== undefined && (
            <Panel
              title={
                wasNextMoveAMistake
                  ? `Podías haber jugado, en vez de ${nextAnalyzedMove.san}`
                  : "Lo que propone el motor aquí"
              }
              bodyClassName=""
            >
              {positionAlternatives.length > 0 ? (
                <EngineLineList
                  lines={positionAlternatives}
                  playedUci={nextAnalyzedMove.uci}
                  onPreviewLine={setPreviewPvUci}
                />
              ) : (
                /* Un análisis anterior a RF-10.1 cuyas posiciones ya no estén
                   en la caché no guardó las líneas: se dice, en vez de dejar el
                   hueco donde en las demás posiciones hay una lista (C-3). */
                <div className="p-3">
                  <EmptyState title="Sin alternativas guardadas">
                    Este análisis solo guardó la mejor jugada, y sus posiciones ya no están en la
                    caché del motor. Reanaliza la partida para ver las alternativas.
                  </EmptyState>
                </div>
              )}
            </Panel>
          )}

          {analysis?.status === "done" && (
            <CriticalMoments
              moments={analysis.critical_moments}
              currentPly={currentPly}
              startingPly={startingPly}
              onSelectPly={goTo}
            />
          )}

          <Panel bodyClassName="p-2">
            {analysis?.status === "done" ? (
              <MoveList
                moves={analysis.moves}
                currentPly={currentPly}
                startingPly={startingPly}
                onSelectPly={goTo}
              />
            ) : (
              <PlainMoveList
                positions={positions}
                currentPly={currentPly}
                startingPly={startingPly}
                onSelectPly={goTo}
              />
            )}
          </Panel>

          {!analysis && !existingQuery.isPending && !existingQuery.isError && (
            <EmptyState title="Sin analizar">
              Pulsa <strong>Analizar</strong> para que el motor evalúe cada jugada.
            </EmptyState>
          )}

          {comparisonQuery.data && (
            <EngineComparison
              comparison={comparisonQuery.data}
              startingPly={startingPly}
              onSelectPly={goTo}
            />
          )}

          {!canCompareEngines && analysis?.status === "done" && (
            <EmptyState title="Sin comparación de motores">
              Analiza también con el otro motor para ver dónde discrepan.
            </EmptyState>
          )}

          {analysis?.status === "done" && (
            <ClassificationSummary
              counts={countClassifications(analysis.moves.map((m) => m.classification))}
            />
          )}
        </aside>
      </div>
    </div>
  );
}

/** Lista de jugadas cuando todavía no hay análisis: solo la notación. */
function PlainMoveList({
  positions,
  currentPly,
  startingPly,
  onSelectPly,
}: {
  positions: ParsedPosition[];
  currentPly: number;
  startingPly: number;
  onSelectPly: (ply: number) => void;
}) {
  return (
    <div className={`flex ${MOVE_LIST_HEIGHT_CLASS} flex-wrap gap-1 overflow-y-auto p-1 text-sm`}>
      {positions.map((position, ply) => (
        <MoveButton key={ply} isCurrent={ply === currentPly} onClick={() => onSelectPly(ply)}>
          {(ply + startingPly) % 2 === 0 && (
            <span className="opacity-50">{moveNumberLabel(ply + startingPly)}</span>
          )}
          {position.san}
        </MoveButton>
      ))}
    </div>
  );
}

function ClassificationSummary({ counts }: { counts: Map<string, number> }) {
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;

  return (
    <Panel title="Resumen de jugadas" bodyClassName="p-3 text-sm">
      <ul className="space-y-1">
        {entries.map(([classification, count]) => {
          const style = classificationStyle(classification);
          return (
            <li key={classification} className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ClassificationBadge classification={classification} />
                {style.label}
              </span>
              <span className="tabular-nums opacity-70">{count}</span>
            </li>
          );
        })}
      </ul>
      {/* Este panel es la leyenda de hecho de las clasificaciones, así que
          lleva su regla escrita, como la tabla de tipos de error del panel de
          estadísticas: "Teoría" no dice por sí solo por qué se aplica
          (criterio C-6 de docs/07-coherencia-ui.md). */}
      <ul className="mt-2 space-y-0.5 border-t border-slate-100 pt-2 text-xs opacity-60 dark:border-slate-800">
        {entries.map(([classification]) => {
          const style = classificationStyle(classification);
          return (
            <li key={classification}>
              <strong className="font-medium">{style.label}:</strong> {style.description}
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

function countClassifications(classifications: string[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const classification of classifications) {
    counts.set(classification, (counts.get(classification) ?? 0) + 1);
  }
  return counts;
}

/** Reconstruye la secuencia de posiciones desde el PGN, para poder navegar la
 * partida aunque todavía no se haya analizado. */
function parsePgn(pgn: string | undefined): ParsedGame {
  const emptyParsedGame: ParsedGame = {
    startingFen: DEFAULT_POSITION,
    positions: [],
  };
  if (!pgn) return emptyParsedGame;
  try {
    const chess = new Chess();
    chess.loadPgn(pgn);
    const history = chess.history({ verbose: true });
    return {
      // `before` de la primera jugada es la posición inicial real: un PGN con
      // `[SetUp "1"]` + `[FEN ...]` (odds chess, Chess960, partidas desde
      // posición) no empieza en la posición estándar. Sin jugadas no hay
      // `before`, pero entonces la posición actual del tablero es la inicial.
      startingFen: history[0]?.before ?? chess.fen(),
      positions: history.map((move) => ({
        fen: move.after,
        lan: move.lan,
        san: move.san,
      })),
    };
  } catch {
    // Un PGN que chess.js no acepta no debe tumbar la página: el resto
    // (cabecera, botón de analizar) sigue siendo útil.
    return emptyParsedGame;
  }
}

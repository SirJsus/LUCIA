/** Visor de una partida (RF-5.1): tablero, jugadas clasificadas, gráfico de
 * evaluación y disparo del análisis con progreso en vivo. */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { Chess, DEFAULT_POSITION } from "chess.js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/Button";
import { EngineSelect } from "../../components/EngineSelect";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { CustomPositionBadge } from "../../components/CustomPositionBadge";
import { BoardWithEvalBar } from "../../components/board/BoardWithEvalBar";
import { EngineLineList } from "../../components/board/EngineLineList";
import { arrowsFromEngineLines, arrowsFromPreviewLine } from "../../components/board/boardConfig";
import { MoveButton } from "../../components/board/MoveButton";
import { MoveNavigator } from "../../components/board/MoveNavigator";
import { useMoveNavigationKeys } from "../../components/board/useMoveNavigationKeys";
import { EmptyState, ErrorBox, ProgressBox, Spinner } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import {
  BOARD_HINT_CLASSES,
  BOARD_SIDEBAR_GRID_CLASS,
  MOVE_LIST_HEIGHT_CLASS,
} from "../../components/styles";
import { api } from "../../lib/api";
import { classificationStyle, MISTAKE_CLASSIFICATIONS } from "../../lib/classification";
import {
  formatAccuracy,
  formatDate,
  formatDuration,
  formatEngineName,
  formatTimeClass,
  gameResult,
  type EngineId,
} from "../../lib/format";
import { moveNumberLabel, plyFromFen } from "../../lib/moves";
import { whiteWinPercentAfterMove } from "../../lib/score";
import { EngineComparison } from "./EngineComparison";
import { EvalChart } from "./EvalChart";
import { MoveList } from "./MoveList";
import { useAnalysisProgress } from "./useAnalysisProgress";

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

  const [currentPly, setCurrentPly] = useState(-1); // -1 = posición inicial
  const [analysisId, setAnalysisId] = useState<number | null>(null);
  const [orientation, setOrientation] = useState<"white" | "black">("white");
  const [engine, setEngine] = useState<EngineId>("stockfish");
  const [previewPvUci, setPreviewPvUci] = useState<string[] | null>(null);

  const gameQuery = useQuery({ queryKey: ["game", id], queryFn: () => api.getGame(id) });

  // Si la partida ya se analizó antes, se reutiliza en vez de volver a
  // gastar minutos de motor.
  const existingQuery = useQuery({
    queryKey: ["analyses", id],
    queryFn: () => api.listAnalyses(id),
  });

  useEffect(() => {
    const done = existingQuery.data?.find((a) => a.status === "done");
    const pending = existingQuery.data?.find(
      (a) => a.status === "queued" || a.status === "running",
    );
    if (analysisId === null && (done || pending)) setAnalysisId((done ?? pending)!.id);
  }, [existingQuery.data, analysisId]);

  const analysisQuery = useQuery({
    queryKey: ["analysis", analysisId],
    queryFn: () => api.getAnalysis(analysisId as number),
    enabled: analysisId !== null,
  });

  const analysis = analysisQuery.data;
  const isRunning = analysis?.status === "queued" || analysis?.status === "running";

  const progress = useAnalysisProgress(isRunning ? analysisId : null, () =>
    analysisQuery.refetch(),
  );
  const elapsedSeconds = useElapsedSeconds(isRunning);

  const analyzeMutation = useMutation({
    mutationFn: () => api.createAnalysis({ game_ids: [id], engine }),
    onSuccess: (created) => {
      setAnalysisId(created[0].id);
      void existingQuery.refetch(); // para que aparezca en el selector de motor
    },
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
  const currentFen = currentPly < 0 ? startingFen : positions[currentPly].fen;
  const lastMoveUci = currentPly < 0 ? null : positions[currentPly].lan;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/" className="text-sm opacity-70 hover:underline">
            ← Volver a partidas
          </Link>
          <h1 className="mt-1 text-2xl font-bold">
            {game.white_username} <span className="opacity-60">({game.white_rating})</span>{" "}
            <span className="font-mono">{gameResult(game)}</span> {game.black_username}{" "}
            <span className="opacity-60">({game.black_rating})</span>
          </h1>
          <p className="flex flex-wrap items-center gap-2 text-sm opacity-60">
            <span>
              {formatDate(game.played_at)} · {formatTimeClass(game.time_class)} ·{" "}
              {game.rated ? "puntuada" : "amistosa"}
            </span>
            {/* Sin esto, un tablero al que le faltan piezas se lee como un
                fallo de la aplicación y no como la partida que es. */}
            {game.starts_from_custom_position && <CustomPositionBadge />}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => setOrientation(orientation === "white" ? "black" : "white")}>
            Girar tablero
          </Button>
          <EngineSelect value={engine} onChange={setEngine} />
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

      {analyzeMutation.isError && <ErrorBox error={analyzeMutation.error} />}
      {existingQuery.isError && (
        <ErrorBox error={existingQuery.error} onRetry={existingQuery.refetch} />
      )}
      {analysis?.status === "error" && (
        <ErrorBox error={new Error(analysis.error ?? "el análisis falló")} />
      )}

      {isRunning && (
        <ProgressBox
          label="Analizando con el motor…"
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
            ← → recorren la partida, Inicio y Fin van a sus extremos. Pulsa una jugada de la lista
            o del gráfico para saltar a esa posición. Señala una jugada de las alternativas para
            verla sobre el tablero.
          </p>

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

/** Segundos que lleva corriendo el análisis, mientras `isRunning` sea cierto.
 *
 * Acompaña a la barra de progreso en vez de sustituirla porque miden cosas
 * distintas: la barra va por posición evaluada, y esas no tardan lo mismo —
 * las que ya están en `position_cache` salen al instante y Lc0 tarda distinto
 * en cada una. El reloj es lo único que dice cuánto se lleva esperado de
 * verdad. Cuenta desde que esta pantalla ve el análisis en marcha, así que al
 * recargar la página empieza de cero; para que sobreviviera habría que
 * exponer `created_at` de la fila `analyses`, que hoy no sale en la API.
 */
function useElapsedSeconds(isRunning: boolean): number {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      setElapsedSeconds(0);
      return;
    }
    const startedAt = Date.now();
    const timer = setInterval(
      () => setElapsedSeconds(Math.round((Date.now() - startedAt) / 1000)),
      1000,
    );
    return () => clearInterval(timer);
  }, [isRunning]);

  return elapsedSeconds;
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
  const emptyParsedGame: ParsedGame = { startingFen: DEFAULT_POSITION, positions: [] };
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

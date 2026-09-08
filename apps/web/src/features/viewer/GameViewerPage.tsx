/** Visor de una partida (RF-5.1): tablero, jugadas clasificadas, gráfico de
 * evaluación y disparo del análisis con progreso en vivo. */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { Chess, DEFAULT_POSITION } from "chess.js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/Button";
import { BoardWithEvalBar } from "../../components/board/BoardWithEvalBar";
import { MoveNavigator } from "../../components/board/MoveNavigator";
import { EmptyState, ErrorBox, ProgressBox, Spinner } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { FIELD_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { classificationStyle } from "../../lib/classification";
import {
  formatAccuracy,
  formatDate,
  formatDuration,
  formatEngineName,
  formatTimeClass,
  gameResult,
} from "../../lib/format";
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
  const [engine, setEngine] = useState<"stockfish" | "lc0">("stockfish");

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

  const goTo = useCallback(
    (ply: number) => setCurrentPly(Math.max(-1, Math.min(ply, positions.length - 1))),
    [positions.length],
  );

  // Navegación con teclado (RF-5.1).
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement) return;
      const actions: Record<string, () => void> = {
        ArrowLeft: () => goTo(currentPly - 1),
        ArrowRight: () => goTo(currentPly + 1),
        Home: () => goTo(-1),
        End: () => goTo(positions.length - 1),
      };
      const action = actions[event.key];
      if (action) {
        event.preventDefault();
        action();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [currentPly, goTo, positions.length]);

  // El análisis guardado solo tiene la mejor jugada de cada posición, no el
  // MultiPV completo (eso vive en el tablero de análisis, que consulta al
  // motor en vivo), así que aquí la flecha es una sola. RF-10 es justamente
  // persistir las alternativas; hasta entonces no hay más que dibujar.
  const bestMoveUci = analysis?.moves[currentPly + 1]?.best_move_uci ?? null;
  const engineArrows = useMemo(
    () => (bestMoveUci ? [{ uci: bestMoveUci, brush: "green" as const }] : []),
    [bestMoveUci],
  );

  // En la posición inicial nadie ha movido todavía: 50-50 mientras haya
  // análisis, y sin barra si no lo hay.
  const currentAnalyzedMove = currentPly >= 0 ? analysis?.moves[currentPly] : undefined;
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
          <h1 className="mt-1 text-xl font-bold">
            {game.white_username} <span className="opacity-60">({game.white_rating})</span>{" "}
            <span className="font-mono">{gameResult(game)}</span> {game.black_username}{" "}
            <span className="opacity-60">({game.black_rating})</span>
          </h1>
          <p className="text-sm opacity-60">
            {formatDate(game.played_at)} · {formatTimeClass(game.time_class)} ·{" "}
            {game.rated ? "puntuada" : "amistosa"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => setOrientation(orientation === "white" ? "black" : "white")}>
            Girar tablero
          </Button>
          <select
            value={engine}
            onChange={(event) => setEngine(event.target.value as "stockfish" | "lc0")}
            title="Motor con el que analizar"
            className={`text-sm ${FIELD_CLASSES}`}
          >
            <option value="stockfish">Stockfish</option>
            <option value="lc0">Lc0</option>
          </select>
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

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-3">
          <BoardWithEvalBar
            fen={currentFen}
            orientation={orientation}
            lastMoveUci={lastMoveUci}
            engineArrows={engineArrows}
            whiteWinPercent={whiteWinPercent}
          />

          <MoveNavigator
            onFirst={() => goTo(-1)}
            onPrevious={() => goTo(currentPly - 1)}
            onNext={() => goTo(currentPly + 1)}
            onLast={() => goTo(positions.length - 1)}
            canGoBack={currentPly > -1}
            canGoForward={currentPly < positions.length - 1}
            position={`${currentPly + 1} / ${positions.length}`}
          />

          {analysis?.status === "done" && analysis.moves.length > 0 && (
            <EvalChart moves={analysis.moves} currentPly={currentPly} onSelectPly={goTo} />
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
                {formatEngineName(analysis.engine)} · profundidad {analysis.depth} · MultiPV{" "}
                {analysis.multipv}
              </p>
            </Panel>
          )}

          <Panel bodyClassName="p-2">
            {analysis?.status === "done" ? (
              <MoveList moves={analysis.moves} currentPly={currentPly} onSelectPly={goTo} />
            ) : (
              <PlainMoveList positions={positions} currentPly={currentPly} onSelectPly={goTo} />
            )}
          </Panel>

          {!analysis && !existingQuery.isPending && (
            <EmptyState title="Sin analizar">
              Pulsa <strong>Analizar</strong> para que el motor evalúe cada jugada.
            </EmptyState>
          )}

          {comparisonQuery.data && (
            <EngineComparison comparison={comparisonQuery.data} onSelectPly={goTo} />
          )}

          {!canCompareEngines && analysis?.status === "done" && (
            <p className="rounded border border-dashed border-slate-300 px-3 py-2 text-xs opacity-70 dark:border-slate-700">
              Analiza también con el otro motor para ver dónde discrepan.
            </p>
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
  onSelectPly,
}: {
  positions: ParsedPosition[];
  currentPly: number;
  onSelectPly: (ply: number) => void;
}) {
  return (
    <div className="flex max-h-[28rem] flex-wrap gap-1 overflow-y-auto p-1 text-sm">
      {positions.map((position, ply) => (
        <button
          key={ply}
          type="button"
          onClick={() => onSelectPly(ply)}
          className={`rounded px-1.5 py-0.5 font-mono hover:bg-slate-100 dark:hover:bg-slate-800 ${
            ply === currentPly ? "bg-indigo-100 font-medium dark:bg-indigo-900/60" : ""
          }`}
        >
          {ply % 2 === 0 && <span className="mr-1 opacity-50">{ply / 2 + 1}.</span>}
          {position.san}
        </button>
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
                <span className={`rounded px-1 text-[10px] leading-4 ${style.className}`}>
                  {style.symbol}
                </span>
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

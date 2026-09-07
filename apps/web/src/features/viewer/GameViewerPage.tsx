/** Visor de una partida (RF-5.1): tablero, jugadas clasificadas, gráfico de
 * evaluación y disparo del análisis con progreso en vivo. */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { api } from "../../lib/api";
import { classificationStyle } from "../../lib/classification";
import { formatAccuracy, formatDate, formatDuration, gameResult } from "../../lib/format";
import { whiteWinPercentAfterMove } from "../../lib/score";
import { Chessboard } from "./Chessboard";
import { EvalBar } from "./EvalBar";
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

const STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

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

  const positions = useMemo(() => parsePgn(gameQuery.data?.pgn), [gameQuery.data?.pgn]);

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
  const currentFen = currentPly < 0 ? STARTING_FEN : positions[currentPly].fen;
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
            {formatDate(game.played_at)} · {game.time_class} · {game.rated ? "puntuada" : "amistosa"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setOrientation(orientation === "white" ? "black" : "white")}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Girar tablero
          </button>
          <select
            value={engine}
            onChange={(event) => setEngine(event.target.value as "stockfish" | "lc0")}
            title="Motor con el que analizar"
            className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="stockfish">Stockfish</option>
            <option value="lc0">Lc0</option>
          </select>
          <button
            type="button"
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending || isRunning}
            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            {isRunning || analyzeMutation.isPending
              ? "Analizando…"
              : doneAnalysisByEngine.has(engine)
                ? `Reanalizar con ${engine}`
                : `Analizar con ${engine}`}
          </button>
        </div>
      </div>

      {analyzeMutation.isError && <ErrorBox error={analyzeMutation.error} />}
      {analysis?.status === "error" && (
        <ErrorBox error={new Error(analysis.error ?? "el análisis falló")} />
      )}

      {isRunning && (
        <div className="rounded border border-indigo-300 bg-indigo-50 px-3 py-2 text-sm dark:border-indigo-800 dark:bg-indigo-950/50">
          <div className="flex justify-between">
            <span>Analizando con el motor…</span>
            <span className="tabular-nums opacity-70">
              {progress ? `posición ${progress.ply} de ${progress.total}` : "en cola"} ·{" "}
              {formatDuration(elapsedSeconds)}
            </span>
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded bg-indigo-200 dark:bg-indigo-900">
            <div
              className="h-full bg-indigo-600 transition-all dark:bg-indigo-400"
              style={{ width: progress ? `${(progress.ply / progress.total) * 100}%` : "0%" }}
            />
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-3">
          <div className="mx-auto flex w-full max-w-[36rem] gap-3">
            {analysis?.status === "done" && (
              <EvalBar whiteWinPercent={whiteWinPercent} orientation={orientation} />
            )}
            <div className="min-w-0 flex-1">
              <Chessboard
                fen={currentFen}
                orientation={orientation}
                lastMoveUci={lastMoveUci}
                engineArrows={engineArrows}
              />
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 text-sm">
            <NavButton
              onClick={() => goTo(-1)}
              disabled={currentPly === -1}
              symbol="⏮"
              accessibleName="Ir a la posición inicial"
            />
            <NavButton
              onClick={() => goTo(currentPly - 1)}
              disabled={currentPly === -1}
              symbol="◀"
              accessibleName="Jugada anterior"
            />
            <span className="w-24 text-center tabular-nums opacity-70">
              {currentPly + 1} / {positions.length}
            </span>
            <NavButton
              onClick={() => goTo(currentPly + 1)}
              disabled={currentPly >= positions.length - 1}
              symbol="▶"
              accessibleName="Jugada siguiente"
            />
            <NavButton
              onClick={() => goTo(positions.length - 1)}
              disabled={currentPly >= positions.length - 1}
              symbol="⏭"
              accessibleName="Ir a la última jugada"
            />
          </div>

          {analysis?.status === "done" && analysis.moves.length > 0 && (
            <EvalChart moves={analysis.moves} currentPly={currentPly} onSelectPly={goTo} />
          )}
        </div>

        <aside className="space-y-3">
          {analysis?.status === "done" && (
            <div className="rounded border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900">
              <p className="mb-2 font-medium">Precisión</p>
              <div className="flex justify-between">
                <span>{game.white_username}</span>
                <span className="tabular-nums">{formatAccuracy(analysis.white_accuracy)}</span>
              </div>
              <div className="flex justify-between">
                <span>{game.black_username}</span>
                <span className="tabular-nums">{formatAccuracy(analysis.black_accuracy)}</span>
              </div>
              <p className="mt-2 text-xs opacity-60">
                {analysis.engine} · profundidad {analysis.depth} · MultiPV {analysis.multipv}
              </p>
            </div>
          )}

          <div className="rounded border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900">
            {analysis?.status === "done" ? (
              <MoveList moves={analysis.moves} currentPly={currentPly} onSelectPly={goTo} />
            ) : (
              <PlainMoveList positions={positions} currentPly={currentPly} onSelectPly={goTo} />
            )}
          </div>

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

/** Botón de navegación del visor. `symbol` es lo que se ve y `accessibleName`
 * lo que se lee: un botón cuyo contenido es solo un símbolo no tiene nombre
 * accesible propio (C-7 de docs/07-coherencia-ui.md). */
function NavButton({
  onClick,
  disabled,
  symbol,
  accessibleName,
}: {
  onClick: () => void;
  disabled: boolean;
  symbol: string;
  accessibleName: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={accessibleName}
      title={accessibleName}
      className="rounded border border-slate-300 px-2.5 py-1 disabled:opacity-40 dark:border-slate-700"
    >
      {symbol}
    </button>
  );
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
    <div className="rounded border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="mb-2 font-medium">Resumen de jugadas</p>
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
    </div>
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
function parsePgn(pgn: string | undefined): ParsedPosition[] {
  if (!pgn) return [];
  try {
    const chess = new Chess();
    chess.loadPgn(pgn);
    return chess.history({ verbose: true }).map((move) => ({
      fen: move.after,
      lan: move.lan,
      san: move.san,
    }));
  } catch {
    // Un PGN que chess.js no acepta no debe tumbar la página: el resto
    // (cabecera, botón de analizar) sigue siendo útil.
    return [];
  }
}

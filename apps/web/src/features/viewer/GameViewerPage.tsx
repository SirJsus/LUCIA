/** Visor de una partida (RF-5.1): tablero, jugadas clasificadas, gráfico de
 * evaluación y disparo del análisis con progreso en vivo. */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { api } from "../../lib/api";
import { classificationStyle } from "../../lib/classification";
import { formatAccuracy, formatDate, gameResult } from "../../lib/format";
import { Chessboard } from "./Chessboard";
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

  const refetchAnalysis = useCallback(() => {
    void analysisQuery.refetch();
  }, [analysisQuery]);

  const progress = useAnalysisProgress(isRunning ? analysisId : null, refetchAnalysis);

  const analyzeMutation = useMutation({
    mutationFn: () => api.createAnalysis({ game_ids: [id], engine }),
    onSuccess: (created) => {
      setAnalysisId(created[0].id);
      void existingQuery.refetch(); // para que aparezca en el selector de motor
    },
  });

  // Con análisis terminados de dos motores distintos se puede comparar (RF-2.6).
  const terminados = (existingQuery.data ?? []).filter((a) => a.status === "done");
  const porMotor = new Map(terminados.map((a) => [a.engine, a]));
  const puedeComparar = porMotor.size >= 2;

  const comparisonQuery = useQuery({
    queryKey: ["comparison", [...porMotor.values()].map((a) => a.id).sort()],
    queryFn: () => {
      const [a, b] = [...porMotor.values()];
      return api.compareAnalyses(a.id, b.id);
    },
    enabled: puedeComparar,
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

  if (gameQuery.isPending) return <Spinner label="Cargando la partida…" />;
  if (gameQuery.isError) return <ErrorBox error={gameQuery.error} onRetry={gameQuery.refetch} />;

  const game = gameQuery.data;
  const currentFen = currentPly < 0 ? STARTING_FEN : positions[currentPly].fen;
  const lastMoveUci = currentPly < 0 ? null : positions[currentPly].lan;
  const bestMoveUci = analysis?.moves[currentPly + 1]?.best_move_uci ?? null;

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
              : porMotor.has(engine)
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
              {progress ? `${progress.ply} / ${progress.total}` : "en cola"}
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
          <div className="mx-auto w-full max-w-[34rem]">
            <Chessboard
              fen={currentFen}
              orientation={orientation}
              lastMoveUci={lastMoveUci}
              bestMoveUci={bestMoveUci}
            />
          </div>

          <div className="flex items-center justify-center gap-2 text-sm">
            <NavButton onClick={() => goTo(-1)} disabled={currentPly === -1} label="⏮" />
            <NavButton onClick={() => goTo(currentPly - 1)} disabled={currentPly === -1} label="◀" />
            <span className="w-24 text-center tabular-nums opacity-70">
              {currentPly + 1} / {positions.length}
            </span>
            <NavButton
              onClick={() => goTo(currentPly + 1)}
              disabled={currentPly >= positions.length - 1}
              label="▶"
            />
            <NavButton
              onClick={() => goTo(positions.length - 1)}
              disabled={currentPly >= positions.length - 1}
              label="⏭"
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

          {!puedeComparar && analysis?.status === "done" && (
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

function NavButton({
  onClick,
  disabled,
  label,
}: {
  onClick: () => void;
  disabled: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="rounded border border-slate-300 px-2.5 py-1 disabled:opacity-40 dark:border-slate-700"
    >
      {label}
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

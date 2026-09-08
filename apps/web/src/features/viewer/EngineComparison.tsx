/** Discrepancias entre dos motores sobre la misma partida (RF-2.6).
 *
 * Donde Stockfish y Lc0 coinciden, la jugada suele estar clara. Donde
 * discrepan hay algo que entender: normalmente una posición donde el cálculo
 * concreto y la valoración posicional apuntan a cosas distintas.
 */
import type { AnalysisComparison } from "@lucia/shared-types";
import { Panel } from "../../components/Panel";
import { classificationStyle } from "../../lib/classification";
import { formatEngineName, formatPercent } from "../../lib/format";

export function EngineComparison({
  comparison,
  onSelectPly,
}: {
  comparison: AnalysisComparison;
  onSelectPly: (ply: number) => void;
}) {
  return (
    <Panel
      title={`${formatEngineName(comparison.engine_a)} vs ${formatEngineName(comparison.engine_b)}`}
      bodyClassName="p-3 text-sm"
    >
      <p className="text-xs opacity-70">
        Coinciden en la mejor jugada en {comparison.agreed_best_moves} de{" "}
        {comparison.total_moves} ({formatPercent(comparison.best_move_agreement_percent)}).
      </p>

      {comparison.disagreements.length === 0 ? (
        <p className="mt-3 text-xs opacity-60">
          No hay diferencias de valoración relevantes: los dos motores ven la partida igual.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {comparison.disagreements.slice(0, 8).map((item) => (
            <li key={item.ply}>
              <button
                type="button"
                onClick={() => onSelectPly(item.ply)}
                className="w-full rounded border border-slate-200 px-2 py-1.5 text-left hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                <div className="flex items-center justify-between">
                  <span>
                    <span className="opacity-50">{Math.floor(item.ply / 2) + 1}.</span>{" "}
                    <span className="font-mono">{item.san}</span>
                  </span>
                  <span className="tabular-nums text-xs opacity-70">
                    {item.win_percent_gap.toFixed(0)} pts de diferencia
                  </span>
                </div>

                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs">
                  <EngineOpinion
                    engine={comparison.engine_a}
                    classification={item.classification_a}
                    winPercent={item.win_percent_after_a}
                    bestMove={item.best_move_a}
                  />
                  <EngineOpinion
                    engine={comparison.engine_b}
                    classification={item.classification_b}
                    winPercent={item.win_percent_after_b}
                    bestMove={item.best_move_b}
                  />
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function EngineOpinion({
  engine,
  classification,
  winPercent,
  bestMove,
}: {
  engine: string;
  classification: string;
  winPercent: number;
  bestMove: string | null;
}) {
  const style = classificationStyle(classification);
  return (
    <span className="flex items-center gap-1">
      <span className="opacity-60">{formatEngineName(engine)}:</span>
      <span className={`rounded px-1 text-[10px] leading-4 ${style.className}`}>
        {style.symbol}
      </span>
      <span className="tabular-nums opacity-70">{formatPercent(winPercent)}</span>
      {bestMove && <span className="font-mono opacity-60">({bestMove})</span>}
    </span>
  );
}

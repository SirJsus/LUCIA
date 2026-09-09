/** Discrepancias entre dos motores sobre la misma partida (RF-2.6).
 *
 * Donde Stockfish y Lc0 coinciden, la jugada suele estar clara. Donde
 * discrepan hay algo que entender: normalmente una posición donde el cálculo
 * concreto y la valoración posicional apuntan a cosas distintas.
 */
import type { AnalysisComparison } from "@lucia/shared-types";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { EmptyState } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { buttonClasses } from "../../components/styles";
import { formatEngineName, formatPercent, formatWinPercentPoints } from "../../lib/format";
import { moveNumberLabel } from "../../lib/moves";

export function EngineComparison({
  comparison,
  startingPly,
  onSelectPly,
}: {
  comparison: AnalysisComparison;
  /** Ply de la posición de partida: la numeración es la de la partida, no la
   * del índice interno (ver `lib/moves.ts`). */
  startingPly: number;
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
      {/* Lo mismo que hace el panel del motor con su encabezado: decir qué es
          cada número antes de enseñarlo (criterio C-6). */}
      {comparison.disagreements.length > 0 && (
        <p className="mt-1 text-xs opacity-60">
          De cada motor: cómo clasifica la jugada, la probabilidad de victoria de las blancas
          después de ella y, entre paréntesis, la jugada que prefería.
        </p>
      )}

      {comparison.disagreements.length === 0 ? (
        // El vacío se dice con el recuadro compartido, como en el resto de la
        // aplicación: era la última frase suelta que hacía de vacío (C-4).
        <div className="mt-3">
          <EmptyState title="Sin discrepancias">
            Los dos motores ven la partida igual: no hay diferencias de valoración relevantes.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-3 space-y-2">
          {comparison.disagreements.slice(0, 8).map((item) => (
            <li key={item.ply}>
              {/* La receta del botón estaba copiada a mano y se había quedado
                  con otro borde y otro `hover` que el resto (C-2). */}
              <button
                type="button"
                onClick={() => onSelectPly(item.ply)}
                className={`${buttonClasses("secondary")} w-full text-left`}
              >
                <div className="flex items-center justify-between">
                  <span>
                    <span className="opacity-50">{moveNumberLabel(item.ply + startingPly)}</span>{" "}
                    <span className="font-mono">{item.san}</span>
                  </span>
                  {/* "pts" a secas se leía como puntos de material, que es lo
                      contrario de lo que mide. */}
                  <span className="text-xs opacity-70">
                    {formatWinPercentPoints(item.win_percent_gap)} de diferencia
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
  return (
    <span className="flex items-center gap-1">
      <span className="opacity-60">{formatEngineName(engine)}:</span>
      <ClassificationBadge classification={classification} />
      <span
        className="tabular-nums opacity-70"
        title="Probabilidad de victoria de las blancas tras la jugada"
      >
        {formatPercent(winPercent)}
      </span>
      {bestMove && (
        <span className="font-mono opacity-60" title="Jugada que prefería este motor">
          ({bestMove})
        </span>
      )}
    </span>
  );
}

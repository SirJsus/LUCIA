/** Las jugadas donde se decidió la partida (RF-2.8).
 *
 * No son "las jugadas malas": una posición en la que solo valía una jugada es
 * crítica tanto si se encontró como si no, y saber que se encontró es la mitad
 * de lo que se viene a aprender. Por eso cada momento dice **por qué** lo es,
 * con la misma etiqueta que usa el resto de la aplicación
 * (`lib/insights.ts`).
 *
 * Los criterios no se calculan aquí: llegan resueltos de la API, que los pide
 * a `lucia_core.insights` sobre lo que ya guardó el análisis.
 */
import type { CriticalMoment } from "@lucia/shared-types";
import { Badge } from "../../components/Badge";
import { EmptyState } from "../../components/Feedback";
import { MoveButton } from "../../components/board/MoveButton";
import { Panel } from "../../components/Panel";
import { formatPercent } from "../../lib/format";
import { criticalMomentStyle } from "../../lib/insights";
import { moveNumberLabel } from "../../lib/moves";
import { whiteWinPercentAfterMove } from "../../lib/score";

/** La probabilidad de victoria **antes** de la jugada, desde el punto de vista
 * de las blancas. `lib/score.ts` tiene la de después, que es la que necesita el
 * resto de la aplicación; aquí hace falta también la de antes, porque un
 * momento crítico se cuenta como un "de aquí a aquí". */
function whiteWinPercentBeforeMove(moment: CriticalMoment): number {
  return moment.color === "white"
    ? moment.win_percent_before
    : 100 - moment.win_percent_before;
}

export function CriticalMoments({
  moments,
  currentPly,
  startingPly,
  onSelectPly,
}: {
  moments: CriticalMoment[];
  currentPly: number;
  /** Ply de la posición de partida, para numerar como el resto de la pantalla. */
  startingPly: number;
  onSelectPly: (ply: number) => void;
}) {
  // Solo se explican los motivos que salen en esta partida: la lista completa
  // sería una leyenda de tres líneas que casi nunca aplican todas.
  const shownKinds = [...new Set(moments.flatMap((moment) => moment.kinds))];

  return (
    <Panel title="Momentos críticos" bodyClassName={moments.length === 0 ? "p-3" : "p-2"}>
      {moments.length === 0 ? (
        <EmptyState title="Ninguno en esta partida">
          Ni la partida cambió de manos, ni hubo posiciones donde solo valiera una jugada.
        </EmptyState>
      ) : (
        <>
          {/* Lo mismo que hacen el panel del motor y la comparación de
              motores: decir qué es cada número antes de enseñarlo, en vez de
              dejarlo en un `title` que solo ve quien pasa el ratón (criterio
              C-6 de docs/07-coherencia-ui.md). */}
          <p className="px-1 pb-1.5 text-xs opacity-60">
            De cada jugada: por qué fue crítica y la probabilidad de victoria de quien movió, antes
            → después.
          </p>
          <ul className="space-y-1 text-sm">
            {moments.map((moment) => (
              <li key={moment.ply} className="flex flex-wrap items-center gap-1.5">
                <MoveButton
                  isCurrent={moment.ply === currentPly}
                  onClick={() => onSelectPly(moment.ply)}
                  title={`Ir a la jugada ${moment.san}`}
                >
                  <span className="opacity-50">{moveNumberLabel(moment.ply + startingPly)}</span>
                  {moment.san}
                </MoveButton>
                {moment.kinds.map((kind) => {
                  const style = criticalMomentStyle(kind);
                  return (
                    <Badge key={kind} tone={style.tone} title={style.description}>
                      {style.label}
                    </Badge>
                  );
                })}
                <span
                  className="ml-auto font-mono text-xs tabular-nums opacity-60"
                  title="Probabilidad de victoria de las blancas, antes y después de la jugada"
                >
                  {formatPercent(whiteWinPercentBeforeMove(moment))} →{" "}
                  {formatPercent(whiteWinPercentAfterMove(moment))}
                </span>
              </li>
            ))}
          </ul>
          {/* La regla de cada motivo, como en "Por qué fallas" del panel de
              estadísticas: en un `title` solo la ve quien pasa el ratón (C-6). */}
          <ul className="mt-2 space-y-0.5 border-t border-slate-100 pt-2 text-xs opacity-60 dark:border-slate-800">
            {shownKinds.map((kind) => {
              const style = criticalMomentStyle(kind);
              return (
                <li key={kind}>
                  <strong className="font-medium">{style.label}:</strong> {style.description}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </Panel>
  );
}

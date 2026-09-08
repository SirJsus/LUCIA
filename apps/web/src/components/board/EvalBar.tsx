/** Barra de evaluación vertical, al lado del tablero (RF-5.2 / RF-6.2).
 *
 * Muestra la evaluación como **probabilidad de victoria**, no en peones: que
 * el motor diga `+3.10` no le dice nada a quien no lee evaluaciones, y además
 * engaña, porque de +3 a +9 la partida ya está igual de ganada. La barra
 * traduce eso a lo único que importa mirando un tablero: cuánto espacio ocupa
 * cada bando.
 *
 * Se orienta como el tablero: el bando que el usuario tiene abajo crece desde
 * abajo. Así la barra y las piezas cuentan la misma historia.
 *
 * La etiqueta es el porcentaje en las dos pantallas que usan la barra. Si en
 * una dijera `+3.10` y en la otra `62 %`, el mismo dato tendría dos formas
 * según dónde se mire (C-5 de docs/07-coherencia-ui.md). La evaluación en
 * peones sigue a la vista en el panel del motor y sobre las flechas, que es
 * donde acompaña a la jugada concreta que la produce.
 *
 * La barra recibe el porcentaje ya calculado, no una evaluación del motor,
 * porque sus dos consumidores lo obtienen de sitios distintos:
 * `GameViewerPage` lo saca del `win_percent_after` que ya trae el análisis
 * guardado (`whiteWinPercentAfterMove`) y `BoardPage` lo deriva de la
 * evaluación en vivo con `whiteWinPercentFromScore` (ADR-0006). Ambos en
 * `lib/score.ts`.
 */
import { formatPercent } from "../../lib/format";

export interface EvalBarProps {
  /** Probabilidad de victoria de las blancas (0-100), o `null` si todavía no
   * hay evaluación (motor apagado, análisis sin terminar). */
  whiteWinPercent: number | null;
  orientation?: "white" | "black";
}

export function EvalBar({ whiteWinPercent, orientation = "white" }: EvalBarProps) {
  const hasEval = whiteWinPercent !== null;
  // Sin evaluación, la barra se queda a la mitad.
  const shownWhiteWinPercent = whiteWinPercent ?? 50;
  const bottomShare =
    orientation === "white" ? shownWhiteWinPercent : 100 - shownWhiteWinPercent;
  const whiteWinPercentText = formatPercent(shownWhiteWinPercent);

  return (
    <div className="flex w-10 shrink-0 flex-col items-center gap-1">
      <div
        role="img"
        aria-label={
          hasEval
            ? `Evaluación: ${whiteWinPercentText} de probabilidad de victoria para las blancas`
            : "Evaluación: sin datos del motor"
        }
        title={
          hasEval
            ? `${whiteWinPercentText} para las blancas · ${formatPercent(100 - shownWhiteWinPercent)} para las negras`
            : "Sin datos del motor"
        }
        className={`relative w-3 flex-1 overflow-hidden rounded border border-slate-300 bg-slate-700 dark:border-slate-700 dark:bg-slate-950 ${
          hasEval ? "" : "opacity-40"
        }`}
      >
        <div
          className="absolute inset-x-0 bottom-0 bg-slate-50 transition-[height] duration-300 dark:bg-slate-200"
          style={{ height: `${bottomShare}%` }}
        />
        {/* La mitad marca el equilibrio: sin ella, un 55 % y un 45 % se ven
            iguales. */}
        <div className="absolute inset-x-0 top-1/2 border-t border-dashed border-slate-400 opacity-60" />
      </div>
      <span className="w-full text-center font-mono text-xs tabular-nums opacity-70">
        {hasEval ? whiteWinPercentText : "—"}
      </span>
    </div>
  );
}

/** La probabilidad de victoria, tablas y derrota que da el **motor** (RF-2.6).
 *
 * Es un dato distinto del que enseña `EvalBar`, y por eso se ve distinto. La
 * barra de evaluación reparte el tablero entre dos bandos a partir de una
 * fórmula sobre el centipeón, igual para cualquier motor; esto son tres
 * números que contesta el motor por su cuenta, y el tramo del medio —las
 * tablas— es justamente lo que la fórmula no sabe decir. El caso que motiva el
 * requerimiento es la posición que Stockfish puntúa como ganada y la red de
 * Lc0 ve como tablas técnicas: en la barra de evaluación las dos se parecen, y
 * aquí se ven al primer vistazo.
 *
 * La comparten el panel de líneas del motor (`EngineLineList`, en las dos
 * pantallas con tablero) y la comparación de motores del visor
 * (`EngineComparison`), para que el mismo dato se lea igual en los tres sitios
 * (criterio C-5 de docs/07-coherencia-ui.md).
 *
 * Los tres tramos llevan su porcentaje en el `title` y en el nombre accesible,
 * y el texto de al lado repite el de victoria: el significado no puede
 * descansar solo en tres colores (criterios C-6 y C-7).
 */
import type { Wdl } from "@lucia/shared-types";
import { formatPercent } from "../lib/format";

/** Los mismos blancos y negros de la barra de evaluación, para que los dos
 * bandos se reconozcan entre las dos barras; las tablas van en un gris que no
 * es de nadie. */
const SEGMENT_CLASSES = {
  win: "bg-slate-50 dark:bg-slate-200",
  draw: "bg-slate-400 dark:bg-slate-500",
  loss: "bg-slate-700 dark:bg-slate-950",
} as const;

/** El motor informa en partes por mil; la interfaz habla en porcentaje. */
function toPercent(perMille: number): number {
  return perMille / 10;
}

export function WdlBar({ wdl }: { wdl: Wdl }) {
  const segments = [
    { key: "win", percent: toPercent(wdl.win), label: "ganan las blancas" },
    { key: "draw", percent: toPercent(wdl.draw), label: "tablas" },
    { key: "loss", percent: toPercent(wdl.loss), label: "ganan las negras" },
  ] as const;
  const description = segments
    .map((segment) => `${formatPercent(segment.percent)} ${segment.label}`)
    .join(", ");

  return (
    <span className="flex items-center gap-1.5">
      <span
        role="img"
        aria-label={`Según el motor: ${description}`}
        title={`Según el motor: ${description}`}
        className="flex h-2 w-16 shrink-0 overflow-hidden rounded-full border border-slate-300 dark:border-slate-700"
      >
        {segments.map((segment) => (
          <span
            key={segment.key}
            className={SEGMENT_CLASSES[segment.key]}
            style={{ width: `${segment.percent}%` }}
          />
        ))}
      </span>
      {/* Solo el de victoria en texto: los tres cabrían, pero esto va dentro de
          una lista de líneas y tres números por fila la vuelven ilegible. Los
          otros dos están en el `title` y en el nombre accesible. */}
      <span className="font-mono text-xs tabular-nums opacity-70">
        {formatPercent(toPercent(wdl.win))}
      </span>
    </span>
  );
}

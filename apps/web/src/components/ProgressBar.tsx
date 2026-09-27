/** La barra que dibuja cuánto va de algo.
 *
 * Estaba solo dentro de `ProgressBox` —el recuadro de "estoy trabajando"— y el
 * plan semanal (RF-4.5) necesitaba la misma barra para otra cosa: cuánto
 * llevas hecho de los deberes de la semana. Copiarla habría dejado dos barras
 * con el mismo alto y el mismo redondeo sostenidos a mano, que es la familia
 * de incoherencias de las filas 39 a 41 (criterio C-2 de
 * docs/07-coherencia-ui.md).
 *
 * Lo que cambia entre las dos es **de quién es el avance**, y eso es lo que
 * distingue el tono: `system` es lo que lleva hecho la aplicación y `player`
 * lo que lleva hecho quien entrena. La forma es una sola.
 *
 * Los tonos se llaman por su dueño y no por su estado —`done` diría que la
 * barra está terminada, y la de los deberes lo normal es que vaya por la
 * mitad—, que además es como se lee el `status` de un análisis.
 */

export type ProgressBarTone = "system" | "player";

const TONE_CLASSES: Record<ProgressBarTone, { track: string; fill: string }> = {
  system: { track: "bg-indigo-200 dark:bg-indigo-900", fill: "bg-indigo-600 dark:bg-indigo-400" },
  player: { track: "bg-slate-200 dark:bg-slate-700", fill: "bg-emerald-600 dark:bg-emerald-400" },
};

export function ProgressBar({
  percent,
  label,
  valueText,
  tone = "system",
  className = "",
}: {
  /** De 0 a 100, o `null` cuando el trabajo está encolado o no se sabe cuánto
   * queda: entonces la barra se muestra indeterminada en vez de fingir un
   * 0 %. */
  percent: number | null;
  /** Qué avanza, para quien la oye en vez de verla (criterio C-7). */
  label: string;
  /** El avance en sus propias unidades ("3 de 10 puzzles"), cuando el
   * porcentaje no es lo que dice el número de al lado. */
  valueText?: string;
  tone?: ProgressBarTone;
  className?: string;
}) {
  const { track, fill } = TONE_CLASSES[tone];
  return (
    <div
      className={`h-1.5 overflow-hidden rounded ${track} ${className}`}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent ?? undefined}
      aria-valuetext={valueText}
      aria-label={label}
    >
      <div
        className={`h-full ${fill} ${percent === null ? "w-1/3 animate-pulse" : "transition-all"}`}
        style={percent === null ? undefined : { width: `${percent}%` }}
      />
    </div>
  );
}

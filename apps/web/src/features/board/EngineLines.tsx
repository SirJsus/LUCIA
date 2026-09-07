/** Líneas del motor para la posición actual (RF-6.2), con evaluación desde el
 * punto de vista de las blancas, como es costumbre en ajedrez.
 *
 * Recorrer una línea con el ratón o con el tabulador la previsualiza sobre el
 * tablero: al señalar la jugada n se dibujan las n primeras de esa línea. Sin
 * eso hay que reconstruir "Cf3 d5 c4 e6" mentalmente, que es justo lo que no
 * puede hacer quien todavía no lee bien una variante.
 */
import type { EngineLine } from "@lucia/shared-types";
import { EmptyState } from "../../components/Feedback";
import { formatScore } from "../../lib/score";

export function EngineLines({
  lines,
  isLoading,
  onPlayMove,
  onPreviewLine,
}: {
  lines: EngineLine[] | undefined;
  isLoading: boolean;
  onPlayMove: (san: string) => void;
  /** Continuación a dibujar en el tablero, o `null` para dejar de dibujarla. */
  onPreviewLine: (pvUci: string[] | null) => void;
}) {
  return (
    <div className="rounded border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 text-sm font-medium dark:border-slate-800">
        <span>Motor</span>
        {isLoading && <span className="text-xs font-normal opacity-60">analizando…</span>}
      </div>

      {!lines?.length && !isLoading && (
        <div className="p-3">
          <EmptyState title="Sin líneas para esta posición">
            El motor no propone ninguna jugada aquí.
          </EmptyState>
        </div>
      )}

      <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
        {lines?.map((line) => (
          <li
            key={line.rank}
            className="flex gap-2 px-3 py-2"
            onMouseLeave={() => onPreviewLine(null)}
            onBlur={() => onPreviewLine(null)}
          >
            <span className="w-14 shrink-0 font-mono tabular-nums">{formatScore(line)}</span>
            <span className="flex flex-wrap gap-x-1.5 gap-y-0.5">
              {line.pv_san.slice(0, 12).map((san, index) => (
                <button
                  key={`${line.rank}-${index}`}
                  type="button"
                  // Solo la primera jugada es aplicable desde la posición
                  // actual; el resto ya depende de las anteriores. Aun así
                  // todas se pueden señalar para previsualizarlas, y por eso
                  // no se deshabilitan: un botón deshabilitado no recibe
                  // ratón ni foco.
                  onClick={() => index === 0 && onPlayMove(san)}
                  onMouseEnter={() => onPreviewLine(line.pv_uci.slice(0, index + 1))}
                  onFocus={() => onPreviewLine(line.pv_uci.slice(0, index + 1))}
                  className={`rounded px-0.5 font-mono hover:bg-slate-100 dark:hover:bg-slate-800 ${
                    index === 0 ? "" : "opacity-70"
                  }`}
                  title={
                    index === 0
                      ? "Jugar esta jugada"
                      : "Señala para ver la línea hasta aquí en el tablero"
                  }
                >
                  {san}
                </button>
              ))}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

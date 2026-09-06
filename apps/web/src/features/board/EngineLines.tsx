/** Líneas del motor para la posición actual (RF-6.2), con evaluación desde el
 * punto de vista de las blancas, como es costumbre en ajedrez. */
import type { EngineLine } from "@lucia/shared-types";
import { formatScore } from "../../lib/score";

export function EngineLines({
  lines,
  isLoading,
  onPlayMove,
}: {
  lines: EngineLine[] | undefined;
  isLoading: boolean;
  onPlayMove: (san: string) => void;
}) {
  return (
    <div className="rounded border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 text-sm font-medium dark:border-slate-800">
        <span>Motor</span>
        {isLoading && <span className="text-xs font-normal opacity-60">analizando…</span>}
      </div>

      {!lines?.length && !isLoading && (
        <p className="px-3 py-3 text-sm opacity-60">Sin líneas para esta posición.</p>
      )}

      <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
        {lines?.map((line) => (
          <li key={line.rank} className="flex gap-2 px-3 py-2">
            <span className="w-14 shrink-0 font-mono tabular-nums">{formatScore(line)}</span>
            <span className="flex flex-wrap gap-x-1.5 gap-y-0.5">
              {line.pv_san.slice(0, 12).map((san, index) => (
                <button
                  key={`${line.rank}-${index}`}
                  type="button"
                  // Solo la primera jugada es aplicable desde la posición
                  // actual; el resto ya depende de las anteriores.
                  disabled={index > 0}
                  onClick={() => onPlayMove(san)}
                  className="font-mono enabled:hover:underline disabled:opacity-70"
                  title={index === 0 ? "Jugar esta jugada" : undefined}
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

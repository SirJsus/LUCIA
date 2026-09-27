/** Estados compartidos de la interfaz: carga, trabajo en curso, error, éxito,
 * aviso y vacío. Están aquí para no repetirlos —ni reinventarlos— en cada
 * pantalla (criterios C-3 y C-4 de docs/07-coherencia-ui.md).
 *
 * Los cuatro recuadros de color comparten forma y solo cambian de paleta, para
 * que se reconozcan como la misma familia a simple vista.
 */
import type { ReactNode } from "react";
import { ProgressBar } from "./ProgressBar";

export function Spinner({ label = "Cargando…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-sm opacity-70" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      {label}
    </div>
  );
}

type NoticeTone = "error" | "success" | "warning" | "progress";

const TONE_CLASSES: Record<NoticeTone, string> = {
  error:
    "border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200",
  success:
    "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200",
  warning:
    "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-200",
  progress:
    "border-indigo-300 bg-indigo-50 text-indigo-900 dark:border-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-100",
};

function Notice({
  tone,
  children,
  className = "",
}: {
  tone: NoticeTone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded border px-3 py-2 text-sm ${TONE_CLASSES[tone]} ${className}`}>
      {children}
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <Notice tone="error" className="py-3">
      {/* `role="alert"` para que un lector de pantalla lo anuncie al aparecer:
          los errores suelen surgir lejos de donde está el foco. */}
      <p className="font-medium" role="alert">
        Algo falló
      </p>
      <p className="mt-1 opacity-90">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded border border-red-400 px-2 py-1 text-xs hover:bg-red-100 dark:border-red-700 dark:hover:bg-red-900"
        >
          Reintentar
        </button>
      )}
    </Notice>
  );
}

/** Confirmación de que algo salió bien. Antes había tres formas distintas de
 * decirlo —recuadro verde, texto verde suelto y texto gris— y ninguna
 * compartida. */
export function SuccessBox({ children }: { children: ReactNode }) {
  return (
    <Notice tone="success">
      <span role="status">{children}</span>
    </Notice>
  );
}

/** Advertencia: algo funciona, pero con una limitación que conviene saber. */
export function WarningBox({ children }: { children: ReactNode }) {
  return <Notice tone="warning">{children}</Notice>;
}

/** "Estoy trabajando, y esto es lo que llevo".
 *
 * `progress` va de 0 a 100, o `null` cuando el trabajo está encolado o no se
 * sabe cuánto queda. `detail` es el texto de la derecha (posición actual,
 * tiempo transcurrido). La barra es la compartida (`ProgressBar`), la misma
 * que enseña el avance de los deberes del plan semanal. */
export function ProgressBox({
  label,
  detail,
  progress,
}: {
  label: string;
  detail?: ReactNode;
  progress: number | null;
}) {
  return (
    <Notice tone="progress">
      <div className="flex justify-between gap-3">
        <span role="status">{label}</span>
        {detail && <span className="tabular-nums opacity-70">{detail}</span>}
      </div>
      <ProgressBar percent={progress} label={label} className="mt-1.5" />
    </Notice>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded border border-dashed border-slate-300 p-8 text-center dark:border-slate-700">
      <p className="font-medium">{title}</p>
      {children && <div className="mt-2 text-sm opacity-70">{children}</div>}
    </div>
  );
}

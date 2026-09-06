/** Estados compartidos de carga, error y vacío, para no repetirlos en cada página. */
import type { ReactNode } from "react";

export function Spinner({ label = "Cargando…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-sm opacity-70" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      {label}
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <div className="rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200">
      <p className="font-medium">Algo falló</p>
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
    </div>
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

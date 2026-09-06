/** Configuración de los motores (RF-5.4).
 *
 * La ruta del binario se muestra pero no se edita: aceptarla desde el
 * navegador sería ejecutar un ejecutable arbitrario del sistema. Se cambia
 * en `.env` (STOCKFISH_PATH / LC0_PATH) y se recarga la API.
 */
import type { EngineConfigOut, EngineConfigUpdate } from "@lucia/shared-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ErrorBox, Spinner } from "../../components/Feedback";
import { api } from "../../lib/api";

export function EnginesPage() {
  const configQuery = useQuery({ queryKey: ["engines"], queryFn: api.getEnginesConfig });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Motores</h1>
        <p className="mt-1 text-sm opacity-70">
          Estos valores se usan como predeterminados al analizar. Subir profundidad da mejor
          análisis pero tarda mucho más; los hilos no deberían superar los núcleos de tu CPU.
        </p>
      </div>

      {configQuery.isPending && <Spinner />}
      {configQuery.isError && <ErrorBox error={configQuery.error} onRetry={configQuery.refetch} />}

      {configQuery.data && (
        <div className="grid gap-4 lg:grid-cols-2">
          <EngineCard config={configQuery.data.stockfish} />
          <EngineCard config={configQuery.data.lc0} />
        </div>
      )}
    </div>
  );
}

function EngineCard({ config }: { config: EngineConfigOut }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<EngineConfigUpdate>({
    threads: config.threads,
    hash_mb: config.hash_mb,
    depth: config.depth,
    multipv: config.multipv,
  });

  // Si otra pestaña (o el propio guardado) cambia la config, el formulario
  // debe reflejar lo que hay en el servidor, no quedarse en lo que se tecleó.
  useEffect(() => {
    setForm({
      threads: config.threads,
      hash_mb: config.hash_mb,
      depth: config.depth,
      multipv: config.multipv,
    });
  }, [config.threads, config.hash_mb, config.depth, config.multipv]);

  const saveMutation = useMutation({
    mutationFn: () => api.updateEngineConfig(config.name, form),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["engines"] }),
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        saveMutation.mutate();
      }}
      className="space-y-4 rounded border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
    >
      <header className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold capitalize">{config.name}</h2>
          <p className="mt-0.5 break-all font-mono text-xs opacity-60">{config.path}</p>
        </div>
        <AvailabilityBadge available={config.available} />
      </header>

      {!config.available && (
        <p className="rounded border border-amber-300 bg-amber-50 px-2 py-1.5 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-200">
          El binario no está en esa ruta. Ejecuta <code>make engines</code> para compilarlo.
        </p>
      )}

      {config.weights_path && (
        <div className="text-xs">
          <p className="opacity-70">Red neuronal</p>
          <p className="break-all font-mono opacity-60">{config.weights_path}</p>
          {config.weights_available === false && (
            <p className="mt-1 text-amber-700 dark:text-amber-300">
              Falta el archivo de red; Lc0 no podrá analizar.
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <NumberField
          label="Profundidad"
          hint="1–40"
          value={form.depth}
          min={1}
          max={40}
          onChange={(depth) => setForm({ ...form, depth })}
        />
        <NumberField
          label="MultiPV"
          hint="líneas a calcular, 1–10"
          value={form.multipv}
          min={1}
          max={10}
          onChange={(multipv) => setForm({ ...form, multipv })}
        />
        <NumberField
          label="Hilos"
          hint="1–64"
          value={form.threads}
          min={1}
          max={64}
          onChange={(threads) => setForm({ ...form, threads })}
        />
        <NumberField
          label="Hash (MB)"
          hint="16–8192"
          value={form.hash_mb}
          min={16}
          max={8192}
          step={16}
          onChange={(hash_mb) => setForm({ ...form, hash_mb })}
        />
      </div>

      {saveMutation.isError && <ErrorBox error={saveMutation.error} />}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={saveMutation.isPending}
          className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {saveMutation.isPending ? "Guardando…" : "Guardar"}
        </button>
        {saveMutation.isSuccess && (
          <span className="text-sm text-emerald-700 dark:text-emerald-300">Guardado</span>
        )}
      </div>
    </form>
  );
}

function AvailabilityBadge({ available }: { available: boolean }) {
  return (
    <span
      className={`whitespace-nowrap rounded px-2 py-0.5 text-xs ${
        available
          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200"
          : "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200"
      }`}
    >
      {available ? "disponible" : "no encontrado"}
    </span>
  );
}

function NumberField({
  label,
  hint,
  value,
  min,
  max,
  step = 1,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="text-sm">
      <span className="block">{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-950"
      />
      <span className="mt-0.5 block text-xs opacity-50">{hint}</span>
    </label>
  );
}

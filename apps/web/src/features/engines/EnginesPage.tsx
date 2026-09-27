/** Configuración de los motores (RF-5.4).
 *
 * La ruta del binario se muestra pero no se edita: aceptarla desde el
 * navegador sería ejecutar un ejecutable arbitrario del sistema. Se cambia
 * en `.env` (STOCKFISH_PATH / LC0_PATH) y se recarga la API.
 */
import type { EngineConfigOut, EngineConfigUpdate } from "@lucia/shared-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { FieldLabel } from "../../components/FieldLabel";
import { ErrorBox, Spinner, SuccessBox, WarningBox } from "../../components/Feedback";
import { FIELD_CLASSES, PANEL_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatEngineName } from "../../lib/format";

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

      {configQuery.isPending && <Spinner label="Cargando la configuración…" />}
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

  /** Cambiar un campo borra el resultado del guardado anterior: si no, el
   * recuadro seguía diciendo "Configuración guardada" al lado de valores que
   * ya no eran los guardados (criterio C-3). */
  function updateForm(patch: Partial<EngineConfigUpdate>) {
    saveMutation.reset();
    setForm((current) => ({ ...current, ...patch }));
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        saveMutation.mutate();
      }}
      className={`space-y-4 p-4 ${PANEL_CLASSES}`}
    >
      <header className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">{formatEngineName(config.name)}</h2>
          <p className="mt-0.5 break-all font-mono text-xs opacity-60">{config.path}</p>
          {config.backend && (
            <p className="mt-0.5 text-xs opacity-60">backend: {config.backend}</p>
          )}
        </div>
        <AvailabilityBadge available={config.available} />
      </header>

      {!config.available && (
        <WarningBox>
          El binario no está en esa ruta. Ejecuta <code>make engines</code> para compilarlo.
        </WarningBox>
      )}

      {config.limit_kind === "nodes" && (
        <WarningBox>
          Lc0 explora con MCTS, así que el esfuerzo se mide en <strong>nodos</strong>, no en
          profundidad. En CPU con una red grande va muy lento (medido: ~200 nodos por posición
          y minuto), así que sirve para consultar posiciones sueltas, no para analizar partidas
          enteras. Con GPU (LC0_BACKEND=cuda) o una red pequeña cambia por completo.
        </WarningBox>
      )}

      {config.weights_path && (
        <div className="text-xs">
          <p className="opacity-70">Red neuronal</p>
          <p className="break-all font-mono opacity-60">{config.weights_path}</p>
          {config.weights_available === false && (
            <div className="mt-1">
              <WarningBox>Falta el archivo de red; Lc0 no podrá analizar.</WarningBox>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <NumberField
          label={config.limit_kind === "nodes" ? "Nodos" : "Profundidad"}
          hint={config.limit_kind === "nodes" ? "1–40 (¡ojo, ver abajo!)" : "1–40"}
          value={form.depth}
          min={1}
          max={40}
          onChange={(depth) => updateForm({ depth })}
        />
        <NumberField
          label="MultiPV"
          hint="líneas a calcular, 1–10"
          value={form.multipv}
          min={1}
          max={10}
          onChange={(multipv) => updateForm({ multipv })}
        />
        <NumberField
          label="Hilos"
          hint="1–64"
          value={form.threads}
          min={1}
          max={64}
          onChange={(threads) => updateForm({ threads })}
        />
        <NumberField
          label="Hash (MB)"
          hint="16–8192"
          value={form.hash_mb}
          min={16}
          max={8192}
          step={16}
          onChange={(hash_mb) => updateForm({ hash_mb })}
        />
      </div>

      {saveMutation.isError && <ErrorBox error={saveMutation.error} />}

      <div className="flex items-center gap-3">
        <Button type="submit" variant="primary" disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Guardando…" : "Guardar"}
        </Button>
        {saveMutation.isSuccess && <SuccessBox>Configuración guardada.</SuccessBox>}
      </div>
    </form>
  );
}

function AvailabilityBadge({ available }: { available: boolean }) {
  return (
    <Badge tone={available ? "success" : "danger"}>
      {available ? "disponible" : "no encontrado"}
    </Badge>
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
    <FieldLabel label={label} hint={hint}>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.target.value))}
        className={`w-full ${FIELD_CLASSES}`}
      />
    </FieldLabel>
  );
}

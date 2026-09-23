/** Drill de aperturas (RF-4.2): repetir jugando las líneas donde peor se rinde.
 *
 * El ciclo de la pantalla es el de los puzzles, y a propósito: se generan las
 * líneas a partir de lo que ya se sabe, se piden las que tocan hoy y se
 * recorren una a una con repetición espaciada. Recorrer una línea está en
 * `DrillRunner`; aquí viven la cola, los estados por los que pasa la pantalla
 * y el botón de generar.
 *
 * **Las dos barajas llegan mezcladas en la misma cola**, ordenadas por cuándo
 * toca repasarlas y no por su origen: para quien entrena son lo mismo —una
 * línea que hay que reproducir— y separarlas obligaría a elegir por cuál
 * empezar cada día. De cuál viene cada una lo dice su insignia.
 *
 * **Depende de la teoría que se haya consultado** (RF-3.6): las líneas salen
 * del repertorio comparado, y esa comparación se llena despacio y a propósito
 * (ADR-0010). Cuando falta teoría, la pantalla lo avisa y manda a refrescarla,
 * en vez de dejar creer que no hay material. El aviso sale de la cola y no de
 * haber pulsado «Generar líneas»: es una condición de la pantalla, porque una
 * cola corta puede serlo porque falta teoría y no porque se juegue bien.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner, SuccessBox, WarningBox } from "../../components/Feedback";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { DrillRunner } from "./DrillRunner";
import { TrainingHeader } from "./TrainingHeader";

const DRILL_QUEUE_QUERY_KEY = ["training", "drills"] as const;

export function DrillsPage() {
  const queryClient = useQueryClient();
  const queueQuery = useQuery({
    queryKey: DRILL_QUEUE_QUERY_KEY,
    queryFn: api.getDrillQueue,
  });
  /** En qué línea de la tanda se está. Se reinicia al traer una tanda nueva. */
  const [queueIndex, setQueueIndex] = useState(0);

  const generateMutation = useMutation({
    mutationFn: () => api.generateDrills(),
    onSuccess: () => {
      setQueueIndex(0);
      queryClient.invalidateQueries({ queryKey: DRILL_QUEUE_QUERY_KEY });
    },
  });

  const queue = queueQuery.data;
  const drill = queue?.drills[queueIndex];

  /** Al terminar una: la siguiente de la tanda, o una tanda nueva si era la
   * última. Se vuelve a pedir en vez de quitarla de la lista en memoria porque
   * el servidor ya sabe cuál vence ahora y cuál acaba de irse a mañana. */
  function goToNextDrill() {
    if (queue && queueIndex + 1 < queue.drills.length) {
      setQueueIndex(queueIndex + 1);
      return;
    }
    setQueueIndex(0);
    queryClient.invalidateQueries({ queryKey: DRILL_QUEUE_QUERY_KEY });
  }

  return (
    <div className="space-y-6">
      <TrainingHeader>
        Las líneas de apertura donde peor te va, para repetirlas jugando. Vuelven espaciadas en el
        tiempo: las que recorres enteras, cada vez más tarde.
      </TrainingHeader>

      <div>
        <div className="flex flex-wrap items-center gap-3">
          {/* Secundario: la acción principal de esta pantalla es recorrer la
              línea que hay debajo, y de primarias hay como mucho una
              (`components/Button.tsx`, criterio C-2). */}
          <Button disabled={generateMutation.isPending} onClick={() => generateMutation.mutate()}>
            {generateMutation.isPending ? "Buscando líneas…" : "Generar líneas"}
          </Button>
          {queue && (
            <span className="text-sm opacity-70">
              {queue.due} por repasar de {queue.total}
            </span>
          )}
        </div>
        <p className="mt-1 text-xs opacity-60">
          Busca líneas nuevas en tu repertorio y en tus aperturas más flojas. No toca las que ya
          tienes, así que pulsarlo de más no cuesta nada.
        </p>
      </div>

      {generateMutation.isError && <ErrorBox error={generateMutation.error} />}
      {generateMutation.isSuccess && (
        <SuccessBox>
          {generateMutation.data.created === 0
            ? "No hay líneas nuevas que añadir."
            : `${generateMutation.data.created} líneas nuevas.`}
        </SuccessBox>
      )}
      {/* Que la teoría esté a medias es una condición de la pantalla y no el
          resultado de haber pulsado un botón: el repertorio se llena a trozos
          (ADR-0010), así que una cola corta puede serlo porque falta teoría y
          no porque se juegue bien. Por eso el aviso sale de la cola y
          acompaña a la pantalla siempre, y no solo tras generar (fila 99 del
          inventario, criterio C-3). */}
      {queue !== undefined && queue.positions_missing > 0 && (
        <WarningBox>
          Faltan {queue.positions_missing} posiciones de teoría por consultar, así que puede haber
          más líneas de las que se ven. Tráelas desde{" "}
          <Link to="/stats" className="underline">
            Estadísticas
          </Link>
          , en la comparación de repertorio.
        </WarningBox>
      )}

      {queueQuery.isPending && <Spinner label="Cargando tus líneas…" />}
      {queueQuery.isError && <ErrorBox error={queueQuery.error} onRetry={queueQuery.refetch} />}

      {queue && queue.total === 0 && (
        <EmptyState title="Todavía no tienes líneas que repetir">
          Salen de tu repertorio comparado con la teoría y de las aperturas que peor se te dan.
          Compara tu repertorio en{" "}
          <Link to="/stats" className="underline">
            Estadísticas
          </Link>{" "}
          y pulsa «Generar líneas».
        </EmptyState>
      )}

      {queue && queue.total > 0 && queue.drills.length === 0 && (
        <EmptyState title="Por hoy has terminado">
          {queue.next_due_at
            ? `El próximo repaso toca el ${formatDate(queue.next_due_at)}.`
            : "No queda ninguna pendiente."}
        </EmptyState>
      )}

      {drill && (
        <div className="space-y-2">
          <p className="text-sm opacity-70">
            Línea {queueIndex + 1} de {queue?.drills.length}
          </p>
          <DrillRunner key={drill.id} drill={drill} onNext={goToNextDrill} />
        </div>
      )}
    </div>
  );
}

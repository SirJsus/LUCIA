/** Entrenamiento: los puzzles sacados de los errores propios, con repetición
 * espaciada (RF-4.1, con RF-10.3).
 *
 * El ciclo de la pantalla es el de la API: se generan los puzzles a partir de
 * las partidas ya analizadas, se piden los que tocan hoy y se contestan uno a
 * uno. Resolver un puzzle está en `PuzzleSolver`; aquí viven la cola, los
 * estados por los que pasa la pantalla y el botón de generar.
 *
 * **No genera sola.** Analizar una tanda de partidas no cambia la baraja por
 * sorpresa: quien entrena decide cuándo renovarla. Y como la generación no
 * toca lo que ya existe, pulsar de más no cuesta nada.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner, SuccessBox } from "../../components/Feedback";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { PuzzleSolver } from "./PuzzleSolver";
import { TrainingHeader } from "./TrainingHeader";

const PUZZLE_QUEUE_QUERY_KEY = ["training", "puzzles"] as const;

export function TrainingPage() {
  const queryClient = useQueryClient();
  const queueQuery = useQuery({ queryKey: PUZZLE_QUEUE_QUERY_KEY, queryFn: api.getPuzzleQueue });
  /** En qué puzzle de la tanda se está. Se reinicia al traer una tanda nueva. */
  const [queueIndex, setQueueIndex] = useState(0);

  const generateMutation = useMutation({
    mutationFn: () => api.generatePuzzles(),
    onSuccess: () => {
      setQueueIndex(0);
      queryClient.invalidateQueries({ queryKey: PUZZLE_QUEUE_QUERY_KEY });
    },
  });

  const queue = queueQuery.data;
  const puzzle = queue?.puzzles[queueIndex];

  /** Al terminar uno: el siguiente de la tanda, o una tanda nueva si era el
   * último. Se vuelve a pedir en vez de quitarlo de la lista en memoria
   * porque el servidor ya sabe cuál vence ahora y cuál acaba de irse a
   * mañana. */
  function goToNextPuzzle() {
    if (queue && queueIndex + 1 < queue.puzzles.length) {
      setQueueIndex(queueIndex + 1);
      return;
    }
    setQueueIndex(0);
    queryClient.invalidateQueries({ queryKey: PUZZLE_QUEUE_QUERY_KEY });
  }

  return (
    <div className="space-y-6">
      <TrainingHeader>
        Puzzles sacados de tus propios errores. Vuelven espaciados en el tiempo: los que aciertas,
        cada vez más tarde.
      </TrainingHeader>

      <div>
        <div className="flex flex-wrap items-center gap-3">
          {/* Secundario: la acción principal de esta pantalla es resolver el
              puzzle que hay debajo, y de primarias hay como mucho una
              (`components/Button.tsx`, criterio C-2). */}
          <Button
            disabled={generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
          >
            {generateMutation.isPending ? "Buscando errores…" : "Generar puzzles"}
          </Button>
          {queue && (
            <span className="text-sm opacity-70">
              {queue.due} por repasar de {queue.total}
            </span>
          )}
        </div>
        {/* Qué hace el botón, a la vista y no en un `title`, que con teclado no
            aparece nunca (criterio C-6, la misma razón que cerró la fila 57). */}
        <p className="mt-1 text-xs opacity-60">
          Busca errores nuevos en tus partidas analizadas y añade sus puzzles. No toca los que ya
          tienes, así que pulsarlo de más no cuesta nada.
        </p>
      </div>

      {generateMutation.isError && <ErrorBox error={generateMutation.error} />}
      {generateMutation.isSuccess && (
        <SuccessBox>
          {generateMutation.data.created === 0
            ? "No hay errores nuevos que convertir en puzzles. Analiza más partidas para tener material."
            : `${generateMutation.data.created} puzzles nuevos.`}
        </SuccessBox>
      )}

      {queueQuery.isPending && <Spinner label="Cargando tus puzzles…" />}
      {queueQuery.isError && <ErrorBox error={queueQuery.error} onRetry={queueQuery.refetch} />}

      {queue && queue.total === 0 && (
        <EmptyState title="Todavía no tienes puzzles">
          Salen de los errores que el motor encuentra en tus partidas. Analiza alguna en{" "}
          <Link to="/" className="underline">
            Partidas
          </Link>{" "}
          y pulsa «Generar puzzles».
        </EmptyState>
      )}

      {queue && queue.total > 0 && queue.puzzles.length === 0 && (
        <EmptyState title="Por hoy has terminado">
          {queue.next_due_at
            ? `El próximo repaso toca el ${formatDate(queue.next_due_at)}.`
            : "No queda ninguno pendiente."}
        </EmptyState>
      )}

      {puzzle && (
        <div className="space-y-2">
          <p className="text-sm opacity-70">
            Puzzle {queueIndex + 1} de {queue?.puzzles.length}
          </p>
          <PuzzleSolver key={puzzle.id} puzzle={puzzle} onNext={goToNextPuzzle} />
        </div>
      )}
    </div>
  );
}

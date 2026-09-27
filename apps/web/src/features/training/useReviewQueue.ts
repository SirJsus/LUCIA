/** El ciclo de una pantalla de repaso: traer la tanda que toca hoy, ir de un
 * ejercicio al siguiente y generar más.
 *
 * Lo comparten los puzzles (RF-4.1) y los drills de apertura (RF-4.2) porque
 * es el mismo ciclo —lo dice la API, que les sirve la misma cola— y lo poco
 * que tiene de delicado conviene decirlo una vez:
 *
 * - **Al terminar el último no se quita de la lista en memoria, se vuelve a
 *   pedir**: el servidor ya sabe cuál vence ahora y cuál acaba de irse a
 *   mañana, y restarlo aquí sería llevar la cuenta por segunda vez.
 * - **Generar no altera lo que ya había**, así que lo único que hace falta
 *   tras generar es volver al principio de la tanda y releerla.
 *
 * Lo que cada pantalla dice de todo esto —cómo se llama el ejercicio, qué
 * pone cuando no queda ninguno— es suyo y no pasa por aquí.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

interface ReviewQueueOptions<QueueT, ItemT, GenerationT> {
  queryKey: readonly unknown[];
  fetchQueue: () => Promise<QueueT>;
  /** Dónde vienen los ejercicios dentro de la cola: cada una los llama por su
   * nombre (`puzzles`, `drills`), que es como se leen en la API. */
  itemsOf: (queue: QueueT) => ItemT[];
  generate: () => Promise<GenerationT>;
}

export function useReviewQueue<QueueT, ItemT, GenerationT>({
  queryKey,
  fetchQueue,
  itemsOf,
  generate,
}: ReviewQueueOptions<QueueT, ItemT, GenerationT>) {
  const queryClient = useQueryClient();
  const queueQuery = useQuery({ queryKey, queryFn: fetchQueue });
  /** En qué ejercicio de la tanda se está. */
  const [index, setIndex] = useState(0);

  function askForANewBatch() {
    setIndex(0);
    queryClient.invalidateQueries({ queryKey });
  }

  const generateMutation = useMutation({ mutationFn: generate, onSuccess: askForANewBatch });

  const queue = queueQuery.data;
  const items = queue ? itemsOf(queue) : [];
  return {
    queueQuery,
    queue,
    generateMutation,
    /** El ejercicio que se está haciendo, o `undefined` si la tanda está vacía
     * o todavía no ha llegado. */
    current: items[index],
    /** Cuál de la tanda es, para poder decir "Puzzle 3 de 8". */
    position: index + 1,
    batchSize: items.length,
    goToNext: () => (index + 1 < items.length ? setIndex(index + 1) : askForANewBatch()),
  };
}

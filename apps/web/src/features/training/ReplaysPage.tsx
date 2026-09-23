/** Re-jugar desde el error (RF-4.4): retomar una partida propia desde donde se
 * torció, contra el motor.
 *
 * **Esta pantalla solo elige.** Retomar abre una partida de sparring normal
 * (RF-4.3) desde otra posición, así que se juega en `SparringGamePage` y vive
 * en la misma tabla: es la misma cosa empezada en otro sitio, no otra forma de
 * jugar.
 *
 * **La lista no se guarda**: se deduce de los análisis que ya hay cada vez que
 * se pregunta, como los patrones de RF-3 (ADR-0008). No lleva ningún estado
 * propio —ni repasos ni progreso—, así que persistirla solo daría una segunda
 * copia que envejecería al reanalizar una partida. Es la decisión contraria a
 * la de los puzzles y los drills, que sí se guardan porque arrastran
 * historial.
 *
 * Aquí salen los errores propios más caros; desde el visor se puede retomar
 * **cualquier** posición de cualquier partida propia. Esta es la versión
 * curada, la que responde a "¿por dónde empiezo?".
 *
 * **Lo que costó el error se enseña abierto**, al revés que en un puzzle sin
 * resolver, que lo esconde porque sería media respuesta (`PuzzleSolver`). No
 * es una incoherencia con su pantalla hermana: aquí no hay nada que adivinar
 * —se viene a jugar otra vez la posición, no a encontrar la jugada— y es
 * justamente el dato que dice por cuál empezar. La API razona lo mismo del
 * lado del servidor (`routers/replays.py::ReplayPositionOut`).
 *
 * Todo esto está razonado en
 * [ADR-0020](../../../../../docs/adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md).
 */
import type { ReplayPosition } from "@lucia/shared-types";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "../../components/Button";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { PanelList } from "../../components/PanelList";
import { buttonClasses, LIST_ROW_CLASSES, LIST_ROW_SUMMARY_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate, formatOwnWinPercentLossSentence } from "../../lib/format";
import { moveNumberLabel, plyFromFen } from "../../lib/moves";
import { SparringSetupForm, type SparringSetup } from "./SparringSetupForm";
import { TrainingHeader } from "./TrainingHeader";

export function ReplaysPage() {
  const navigate = useNavigate();
  /** Desde qué error se está a punto de retomar, por su fila. El formulario de
   * dificultad sale bajo el error elegido y no arriba suelto, para que se vea
   * sobre qué se está decidiendo. */
  const [chosenPositionKey, setChosenPositionKey] = useState<string | null>(null);

  const positionsQuery = useQuery({
    queryKey: ["training", "replays"],
    queryFn: api.getReplayPositions,
  });

  const startMutation = useMutation({
    mutationFn: ({ position, setup }: { position: ReplayPosition; setup: SparringSetup }) =>
      api.startSparringGame({
        ...setup,
        origin: { game_id: position.game_id, ply: position.ply },
      }),
    onSuccess: (game) =>
      navigate({
        to: "/training/sparring/$sparringGameId",
        params: { sparringGameId: String(game.id) },
      }),
  });

  const queue = positionsQuery.data;
  const positions = queue?.positions ?? [];

  return (
    <div className="space-y-6">
      <TrainingHeader>
        Tus errores más caros, para volver a jugarlos contra el motor. Se retoma la partida justo
        antes de la jugada que la torció.
      </TrainingHeader>

      {positionsQuery.isPending && <Spinner label="Buscando tus errores…" />}
      {positionsQuery.isError && (
        <ErrorBox error={positionsQuery.error} onRetry={positionsQuery.refetch} />
      )}

      {positionsQuery.isSuccess && positions.length === 0 && (
        <EmptyState title="Todavía no hay errores que rehacer">
          Salen de los errores que el motor encuentra en tus partidas. Analiza alguna en{" "}
          <Link to="/" className="underline">
            Partidas
          </Link>
          .
        </EmptyState>
      )}

      {/* "Tus errores" y no "Tus peores momentos": "momento" ya nombra otra
          cosa en la aplicación —los momentos críticos del visor (RF-2.8), que
          se eligen con otra regla—, y esta pantalla llama errores a lo que
          enseña en la frase de entrada y en el vacío (criterio C-2). Mismo
          "Tus …" que el listado de Sparring.

          Al lado del título, cuántos se ven de cuántos hay: la lista viene
          recortada a los veinte más caros, y sin decirlo se ven veinte de
          trescientos como si fueran todos, mientras las tres pestañas hermanas
          dicen siempre cuántas quedan de cuántas (fila 102 del inventario,
          criterio C-3). */}
      {positions.length > 0 && (
        <PanelList
          title="Tus errores"
          aside={
            queue !== undefined && queue.total > positions.length ? (
              <span className="text-sm font-normal opacity-70">
                los {positions.length} más caros de {queue.total}
              </span>
            ) : undefined
          }
        >
          {positions.map((position) => {
            const key = `${position.game_id}-${position.ply}`;
            const isChosen = key === chosenPositionKey;
            return (
              <ReplayRow
                key={key}
                position={position}
                isChosen={isChosen}
                isPending={startMutation.isPending}
                // El fallo de la anterior no se hereda al elegir otra: un
                // recuadro rojo sobre un formulario recién abierto se lee
                // como si acabara de fallar este (criterio C-3, el mismo
                // `reset()` que se hizo al abrir "Importar PGN").
                onChoose={() => {
                  startMutation.reset();
                  setChosenPositionKey(key);
                }}
                onCancel={() => setChosenPositionKey(null)}
                onStart={(setup) => startMutation.mutate({ position, setup })}
                startError={isChosen && startMutation.isError ? startMutation.error : null}
              />
            );
          })}
        </PanelList>
      )}
    </div>
  );
}

function ReplayRow({
  position,
  isChosen,
  isPending,
  onChoose,
  onCancel,
  onStart,
  startError,
}: {
  position: ReplayPosition;
  isChosen: boolean;
  isPending: boolean;
  onChoose: () => void;
  onCancel: () => void;
  onStart: (setup: SparringSetup) => void;
  /** El fallo al abrir la partida, que se enseña aquí y no arriba del todo:
   * con veinte errores en la lista, un recuadro en la cabecera queda fuera de
   * la pantalla desde la que se pulsó (criterio C-3). */
  startError: unknown;
}) {
  return (
    <li className={LIST_ROW_CLASSES}>
      <div className={LIST_ROW_SUMMARY_CLASSES}>
        {/* El número de jugada sale del FEN de la posición y no del `ply`, que
            es relativo al inicio de la partida: una partida importada que
            empieza en la jugada 12 se numera desde 12, como ya hace el puzzle
            con la suya (criterio C-5, `lib/moves.ts`). */}
        <span className="font-medium">
          {moveNumberLabel(plyFromFen(position.fen))} {position.san}
        </span>
        <ClassificationBadge classification={position.classification} />
        {/* Lo que costó, en la unidad de siempre y con etiqueta: un número del
            motor suelto no comunica nada (criterios C-5 y C-6). La frase es la
            misma que la del puzzle resuelto y sale del mismo formateador. */}
        <span className="opacity-70">
          {formatOwnWinPercentLossSentence(position.win_percent_before, position.win_percent_after)}
        </span>
        <span className="ml-auto text-xs opacity-60">
          contra {position.opponent}, {formatDate(position.played_at)}
        </span>
        {/* En `sm`, como el enlace de al lado y como los controles de fila de
            los otros dos listados: `md` es el tamaño de una acción de
            cabecera (criterio C-2). Y se llama igual que en el visor, que es
            la otra pantalla desde la que se retoma una posición. */}
        {isChosen ? (
          <Button size="sm" onClick={onCancel}>
            Cancelar
          </Button>
        ) : (
          <Button size="sm" onClick={onChoose}>
            Jugar desde aquí
          </Button>
        )}
        <Link
          to="/games/$gameId"
          params={{ gameId: String(position.game_id) }}
          className={buttonClasses("secondary", "sm")}
        >
          Ver partida
        </Link>
      </div>

      {isChosen && (
        <div className="mt-3 space-y-3 border-t border-slate-100 pt-3 dark:border-slate-800">
          <SparringSetupForm
            defaultPlayerColor={position.player_color === "black" ? "black" : "white"}
            submitLabel="Retomar la partida"
            pendingLabel="Abriendo partida…"
            isPending={isPending}
            onSubmit={onStart}
          />
          {startError !== null && <ErrorBox error={startError} />}
        </div>
      )}
    </li>
  );
}

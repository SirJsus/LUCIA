/** Plan de entrenamiento semanal (RF-4.5): qué falla y qué hacer esta semana.
 *
 * Dos mitades, y en este orden a propósito: primero **qué falla**, con su
 * número, y debajo **los deberes que salen de ahí**, cada uno diciendo qué
 * debilidad lo pide. El requerimiento dice "generado a partir de las
 * debilidades detectadas", así que un deber sin motivo a la vista sería una
 * cuota inventada.
 *
 * **Aquí no se hace nada**: se lee. Cada tarea lleva a la pantalla donde se
 * entrena, y el avance aparece solo — sale de lo que ya está fechado en la
 * base (puzzles y líneas repasados esta semana, partidas jugadas), así que no
 * hay nada que marcar. Por lo mismo, el plan **no se guarda**: se recalcula en
 * cada visita, como los patrones (ADR-0008) y la lista de re-jugar (ADR-0020).
 *
 * La semana empieza en lunes, y es lo que fija desde cuándo cuenta el avance.
 */
import type { PlanTask, Weakness } from "@lucia/shared-types";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Badge } from "../../components/Badge";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { PanelList } from "../../components/PanelList";
import { ProgressBar } from "../../components/ProgressBar";
import { buttonClasses, LIST_ROW_CLASSES, LIST_ROW_SUMMARY_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { mistakeTypeStyle } from "../../lib/insights";
import { formatWeaknessSentence, taskDisplay, taskProgressPercent } from "./plan";
import { TrainingHeader } from "./TrainingHeader";

export function PlanPage() {
  const planQuery = useQuery({ queryKey: ["training", "plan"], queryFn: api.getWeeklyPlan });
  const plan = planQuery.data;

  return (
    <div className="space-y-6">
      <TrainingHeader>
        Qué falla y qué hacer al respecto esta semana. Sale de tus partidas analizadas y se pone al
        día solo: entrenar en las otras pestañas es lo que lo avanza.
      </TrainingHeader>

      {planQuery.isPending && <Spinner label="Mirando tus partidas…" />}
      {planQuery.isError && <ErrorBox error={planQuery.error} onRetry={planQuery.refetch} />}

      {/* Sin análisis no hay diagnóstico, y decir "no tienes debilidades"
          sería felicitar por un plan vacío (criterio C-3). */}
      {plan && plan.analyzed_games === 0 && (
        <EmptyState title="Todavía no puedo decirte qué entrenar">
          El plan sale de tus partidas analizadas y no tienes ninguna. Analiza alguna en{" "}
          <Link to="/" className="underline">
            Partidas
          </Link>
          .
        </EmptyState>
      )}

      {plan && plan.analyzed_games > 0 && (
        <>
          {/* La lista es la compartida (`PanelList`), como los otros tres
              listados de Entrenamiento: la receta a mano —el panel sin
              relleno, la `<ul>` dentro y las clases de la fila— es de las que
              se sostienen copiando y pegando (criterio C-2). El vacío se queda
              dentro de un `Panel` con el mismo título y el mismo recuento
              porque «sobre N partidas analizadas» es justo lo que explica que
              no haya nada que destacar. */}
          {plan.weaknesses.length === 0 ? (
            <Panel
              title="Qué te está costando puntos"
              aside={<AnalyzedGamesCount games={plan.analyzed_games} />}
              bodyClassName="p-3"
            >
              {/* El vacío es el recuadro compartido y no una frase suelta, como
                  en el resto de la aplicación (criterio C-4). */}
              <EmptyState title="No he encontrado nada que destaque">
                Ninguna de las cosas que miro llega a su umbral. Analiza más partidas para afinar
                el diagnóstico.
              </EmptyState>
            </Panel>
          ) : (
            <PanelList
              title="Qué te está costando puntos"
              aside={<AnalyzedGamesCount games={plan.analyzed_games} />}
            >
              {plan.weaknesses.map((weakness, position) => (
                <WeaknessRow
                  key={`${weakness.kind}-${weakness.subject}`}
                  weakness={weakness}
                  isWorst={position === 0}
                />
              ))}
            </PanelList>
          )}

          <div>
            {/* `font-semibold` a secas: es el tamaño con el que se encabeza
                una sección en el resto de la aplicación (criterio C-2). */}
            <h2 className="font-semibold">Tus deberes de esta semana</h2>
            <p className="mt-1 text-xs opacity-60">
              Desde el lunes {formatDate(plan.week_start)}. Se marcan solos: lo que entrenas en las
              otras pestañas cuenta aquí.
            </p>
          </div>

          {plan.tasks.length === 0 ? (
            <EmptyState title="No hay deberes que ponerte">
              {plan.weaknesses.length === 0
                ? "No se ha detectado ninguna debilidad, así que no hay nada que corregir."
                : "Hay cosas que mejorar, pero todavía no tienes material para entrenarlas: genera puzzles o líneas de apertura en sus pestañas."}
            </EmptyState>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {plan.tasks.map((task) => (
                <TaskCard key={task.kind} task={task} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/** Sobre cuántas partidas se hizo el diagnóstico, al lado del título. Es la
 * misma frase con el vacío y con la lista llena: cambia el cuerpo del panel, no
 * lo que se está mirando (criterio C-2). */
function AnalyzedGamesCount({ games }: { games: number }) {
  return (
    <span className="text-sm font-normal opacity-70">
      sobre {games} {games === 1 ? "partida analizada" : "partidas analizadas"}
    </span>
  );
}

function WeaknessRow({ weakness, isWorst }: { weakness: Weakness; isWorst: boolean }) {
  return (
    <li className={`${LIST_ROW_CLASSES} ${LIST_ROW_SUMMARY_CLASSES}`}>
      {/* Por dónde empezar, dicho y no solo insinuado por el orden: una lista
          ordenada no se lee como una prioridad si no lo dice (criterio C-6).
          La primera no es la de número más alto —los cinco números están en
          unidades distintas y no se pueden comparar— sino la más estructural,
          que es el orden fijo que fija `lucia_core.plan`. */}
      {isWorst && <Badge tone="warning">lo primero</Badge>}
      <span>{formatWeaknessSentence(weakness)}</span>
      {weakness.kind === "mistake_type" && (
        <span className="ml-auto text-xs opacity-60">
          {mistakeTypeStyle(weakness.subject).description}
        </span>
      )}
    </li>
  );
}

function TaskCard({ task }: { task: PlanTask }) {
  const { label, unit, to } = taskDisplay(task.kind);
  const progress = taskProgressPercent(task);
  const isDone = task.done_this_week >= task.weekly_target;
  return (
    <Panel
      title={label}
      aside={
        isDone ? <Badge tone="success">hecho</Badge> : <Badge tone="neutral">pendiente</Badge>
      }
    >
      <p className="text-sm">
        {task.done_this_week} de {task.weekly_target} {unit}
      </p>
      {/* La barra repite en forma lo que dice el número, para que el avance se
          vea de un vistazo sin leerlo (criterio C-6). Es la misma que usa el
          recuadro de progreso (`components/ProgressBar.tsx`), en su tono de
          "esto lo llevas hecho tú" (criterio C-2). */}
      <ProgressBar
        percent={progress}
        tone="player"
        label={label}
        valueText={`${task.done_this_week} de ${task.weekly_target} ${unit}`}
        className="mt-2"
      />

      {/* De dónde sale este deber. Es lo que lo separa de una cuota inventada,
          y por eso va en la tarjeta y no escondido. */}
      <ul className="mt-2 space-y-0.5 text-xs opacity-70">
        {task.weaknesses.map((weakness) => (
          <li key={`${weakness.kind}-${weakness.subject}`}>{formatWeaknessSentence(weakness)}</li>
        ))}
      </ul>

      {/* Secundario y en `sm`, como el enlace que abre un elemento en los otros
          cuatro listados ("Ver partida", "Ver tablero"): de primarias hay como
          mucho una por pantalla y aquí hay una tarjeta por deber
          (`components/Button.tsx`, criterio C-2). */}
      <div className="mt-3">
        <Link to={to} className={buttonClasses("secondary", "sm")}>
          Entrenar
        </Link>
      </div>
    </Panel>
  );
}

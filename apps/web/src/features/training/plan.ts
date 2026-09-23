/** Cómo se lee el plan semanal en pantalla (RF-4.5): qué dice cada debilidad
 * y qué dice cada deber.
 *
 * Vive aparte de la pantalla porque es lógica pura y se prueba sola
 * (`__tests__/plan.test.ts`). Lo que traduce son números en cinco unidades
 * distintas —puntos de probabilidad, porcentaje de errores, puntos perdidos,
 * porcentaje de partidas, puntos de precisión— a la frase que explica qué
 * falla: un número del motor suelto no comunica nada (criterio C-6 de
 * docs/07-coherencia-ui.md), y aquí además cada uno se cuenta a su manera.
 *
 * Los cinco números salen de `lib/format.ts` y ninguno se formatea aquí: la
 * unidad de un dato se decide en un solo sitio (criterio C-5).
 */
import type { PlanTask, TrainingTaskKind, Weakness, WeaknessKind } from "@lucia/shared-types";
import {
  formatAccuracyPoints,
  formatPercent,
  formatPhase,
  formatScorePoints,
  formatWinPercentPoints,
} from "../../lib/format";
import { mistakeTypeStyle } from "../../lib/insights";

/** Qué falla, en una frase, con su número. */
export function formatWeaknessSentence(weakness: Weakness): string {
  switch (weakness.kind as WeaknessKind) {
    case "phase":
      return `Pierdes ${formatWinPercentPoints(weakness.magnitude)} por jugada en ${formatPhase(weakness.subject).toLowerCase()}.`;
    case "mistake_type":
      // "clasificados como" y no "de tipo X" en minúscula: las etiquetas de
      // `mistakeTypeStyle` están escritas para ir solas en una insignia ("De
      // final", "Con el reloj encima"), y metidas en el molde daban castellano
      // roto ("son de tipo de final"). Entrecomilladas y tal cual encajan las
      // cuatro, y además se leen igual que la insignia del dashboard (C-5).
      return `El ${formatPercent(weakness.magnitude, 0)} de tus errores están clasificados como «${mistakeTypeStyle(weakness.subject).label}».`;
    case "opening":
      // "frente a empatarlas todas" es la referencia de `points_lost`, y sin
      // ella "pierdes 2.5" no dice pocos o muchos respecto a qué (fila 104 del
      // inventario, criterio C-6).
      return `Con ${weakness.subject} de ${weakness.color === "black" ? "negras" : "blancas"} pierdes ${formatScorePoints(weakness.magnitude)} frente a empatarlas todas.`;
    case "time_trouble":
      return `Juegas con el reloj encima en el ${formatPercent(weakness.magnitude, 0)} de tus partidas.`;
    case "accuracy_trend":
      return `Has perdido ${formatAccuracyPoints(weakness.magnitude)} puntos de precisión respecto a los meses anteriores.`;
  }
}

/** Cómo se llama cada deber, en qué se cuenta y a qué pestaña lleva. Las tres
 * cosas en la misma tabla y no en tres para que el nombre, la unidad y el
 * destino de un deber no puedan separarse.
 *
 * **El nombre es el de la pestaña a la que lleva**, no uno descriptivo: las
 * tarjetas decían "Líneas de apertura", "Posiciones a re-jugar" y "Partidas
 * contra el motor" y se aterrizaba en «Aperturas», «Re-jugar» y «Sparring»,
 * así que el único control que anticipaba el destino —el botón dice "Entrenar"
 * en las cuatro— lo nombraba de otra manera (fila 105 del inventario de
 * docs/07-coherencia-ui.md, criterio C-2). Lo que la tarjeta hace lo cuenta la
 * frase de debajo, que es donde ya estaba. La unidad sí es descriptiva: es lo
 * que se cuenta, no adónde se va. */
type TaskDisplay = { label: string; unit: string; to: string };

const TASK_DISPLAYS: Record<TrainingTaskKind, TaskDisplay> = {
  puzzles: { label: "Puzzles", unit: "puzzles", to: "/training/puzzles" },
  drills: { label: "Aperturas", unit: "líneas", to: "/training/drills" },
  replays: { label: "Re-jugar", unit: "posiciones", to: "/training/replays" },
  sparring: { label: "Sparring", unit: "partidas", to: "/training/sparring" },
};

/** El `kind` llega como texto desde la API, así que uno desconocido se deja
 * pasar con su propio nombre en vez de romper la pantalla. */
export function taskDisplay(kind: string): TaskDisplay {
  return TASK_DISPLAYS[kind as TrainingTaskKind] ?? { label: kind, unit: "", to: "/training" };
}

/** Qué parte del deber va hecha, de 0 a 100, para la barra de progreso. Un
 * objetivo de cero no puede pasar: sin material no hay tarea (RF-4.5), pero si
 * llegara se enseña completa en vez de dividir por cero. */
export function taskProgressPercent(task: PlanTask): number {
  if (task.weekly_target <= 0) return 100;
  return Math.min(100, (task.done_this_week / task.weekly_target) * 100);
}

/** Qué está pasando en el ejercicio, en la insignia del panel lateral de las
 * tres pantallas con tablero de Entrenamiento: el puzzle (RF-4.1), el drill de
 * apertura (RF-4.2) y la partida de sparring (RF-4.3).
 *
 * Está en un solo sitio porque la insignia significaba una cosa distinta en
 * cada pantalla —en qué repaso va el puzzle, de qué baraja salió la línea del
 * drill, de quién es el turno en el sparring—, así que el mismo hueco del
 * mismo panel había que leerlo de tres maneras (fila 98 del inventario de
 * docs/07-coherencia-ui.md). Ahora dice siempre lo mismo: si el sistema está
 * esperando, si te toca a ti o si el ejercicio se acabó (criterios C-2 y C-3).
 * Lo que identifica al ejercicio —el repaso, la apertura, el rival— baja al
 * cuerpo del panel, que es donde se describe lo que se tiene delante.
 *
 * **De dónde sale lo que enseña**: de la pantalla, que es la única que sabe si
 * tiene una petición en vuelo y si el ejercicio sigue abierto. Este componente
 * no consulta nada.
 */
import { Badge } from "../../components/Badge";

export function ExerciseStatusBadge({
  isPlayerTurn,
  isWaitingForServer,
  waitingLabel = "comprobando…",
  finishedLabel = "terminado",
}: {
  /** Si le toca mover a quien entrena. Con el ejercicio cerrado es `false`. */
  isPlayerTurn: boolean;
  /** Si hay una petición en vuelo: el servidor es quien comprueba la jugada en
   * las tres pantallas, así que mientras contesta el tablero está quieto. */
  isWaitingForServer: boolean;
  /** Qué se está esperando, cuando no es solo comprobar: en el sparring la
   * misma petición trae además la respuesta del motor, y decir "comprobando…"
   * ahí escondería que hay un rival pensando. */
  waitingLabel?: string;
  /** Cómo se llama el final, que no es el mismo en las tres: una línea o un
   * puzzle se terminan, una partida se acaba. */
  finishedLabel?: string;
}) {
  if (isWaitingForServer) return <Badge tone="info">{waitingLabel}</Badge>;
  if (isPlayerTurn) return <Badge tone="success">te toca</Badge>;
  return <Badge tone="neutral">{finishedLabel}</Badge>;
}

/** La lista de jugadas de una partida, emparejadas por turno.
 *
 * Es el envoltorio —la rejilla de "número | blancas | negras" con su alto y su
 * scroll— y nada más: **qué hay dentro de cada celda lo decide cada pantalla**.
 * El visor pone un botón con la clasificación de la jugada, porque allí se
 * navega y hay análisis que enseñar; el sparring pone el texto, porque
 * mientras la partida está viva no hay ni lo uno ni lo otro. Lo que sí tiene
 * que ser igual en las dos es cómo se lee la lista (criterio C-2 de
 * docs/07-coherencia-ui.md), y por eso la rejilla está escrita una vez.
 *
 * Agrupar las jugadas en turnos es `turnsOf`, en `lib/moves.ts`, que es donde
 * vive la numeración.
 */
import type { ReactNode } from "react";
import type { Turn } from "../../lib/moves";
import { MOVE_LIST_HEIGHT_CLASS } from "../styles";

interface TurnListProps<MoveT> {
  turns: Turn<MoveT>[];
  /** Cómo se pinta una jugada. Recibe `null` en la celda que falta —el turno
   * a medias del principio o del final—, que es donde la rejilla necesita
   * igualmente algo que ocupe su sitio. */
  renderMove: (move: MoveT | null) => ReactNode;
}

export function TurnList<MoveT>({ turns, renderMove }: TurnListProps<MoveT>) {
  return (
    <ol className={`${MOVE_LIST_HEIGHT_CLASS} overflow-y-auto text-sm`}>
      {turns.map(({ number, white, black }) => (
        <li
          key={number}
          className="grid grid-cols-[2.5rem_1fr_1fr] items-center gap-1 border-b border-slate-100 px-1 py-0.5 dark:border-slate-800"
        >
          <span className="tabular-nums opacity-50">{number}.</span>
          {renderMove(white)}
          {renderMove(black)}
        </li>
      ))}
    </ol>
  );
}

/** Lista de jugadas con su clasificación (RF-5.1), emparejadas por turno.
 *
 * `startingPly` es lo que hay que sumar al ply de cada jugada para llegar al
 * número que se lee en un tablero: en una partida que empieza en la jugada 12
 * (odds chess, Chess960, partidas desde posición) el ply 0 no es "1." Sale de
 * la posición de partida del PGN, en `lib/moves.ts`.
 */
import type { AnalyzedMoveOut } from "@lucia/shared-types";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { MoveButton } from "../../components/board/MoveButton";
import { formatAccuracy } from "../../lib/format";
import { moveNumberOf } from "../../lib/moves";
import { MOVE_LIST_HEIGHT_CLASS } from "../../components/styles";

interface MoveListProps {
  moves: AnalyzedMoveOut[];
  currentPly: number;
  startingPly: number;
  onSelectPly: (ply: number) => void;
}

export function MoveList({ moves, currentPly, startingPly, onSelectPly }: MoveListProps) {
  const turns = groupByTurn(moves, startingPly);

  return (
    <ol className={`${MOVE_LIST_HEIGHT_CLASS} overflow-y-auto text-sm`}>
      {turns.map(({ number, white, black }) => (
        <li
          key={number}
          className="grid grid-cols-[2.5rem_1fr_1fr] items-center gap-1 border-b border-slate-100 py-0.5 dark:border-slate-800"
        >
          <span className="pl-1 tabular-nums opacity-50">{number}.</span>
          <AnalyzedMoveButton move={white} currentPly={currentPly} onSelect={onSelectPly} />
          <AnalyzedMoveButton move={black} currentPly={currentPly} onSelect={onSelectPly} />
        </li>
      ))}
    </ol>
  );
}

function AnalyzedMoveButton({
  move,
  currentPly,
  onSelect,
}: {
  move: AnalyzedMoveOut | undefined;
  currentPly: number;
  onSelect: (ply: number) => void;
}) {
  if (!move) return <span />;

  return (
    <MoveButton isCurrent={move.ply === currentPly} onClick={() => onSelect(move.ply)}>
      <span>{move.san}</span>
      <ClassificationBadge
        classification={move.classification}
        detail={`precisión ${formatAccuracy(move.move_accuracy)}`}
      />
    </MoveButton>
  );
}

interface Turn {
  number: number;
  white?: AnalyzedMoveOut;
  black?: AnalyzedMoveOut;
}

/** El ply 0 es la primera jugada de la partida, que no tiene por qué ser la
 * del turno 1: el número sale de sumarle el ply de la posición de partida. */
function groupByTurn(moves: AnalyzedMoveOut[], startingPly: number): Turn[] {
  const turns: Turn[] = [];
  for (const move of moves) {
    const number = moveNumberOf(move.ply + startingPly);
    let turn = turns.find((t) => t.number === number);
    if (!turn) {
      turn = { number };
      turns.push(turn);
    }
    if (move.color === "white") turn.white = move;
    else turn.black = move;
  }
  return turns;
}

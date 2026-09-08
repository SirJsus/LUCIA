/** Lista de jugadas con su clasificación (RF-5.1), emparejadas por turno. */
import type { AnalyzedMoveOut } from "@lucia/shared-types";
import { classificationStyle } from "../../lib/classification";
import { formatAccuracy } from "../../lib/format";

interface MoveListProps {
  moves: AnalyzedMoveOut[];
  currentPly: number;
  onSelectPly: (ply: number) => void;
}

export function MoveList({ moves, currentPly, onSelectPly }: MoveListProps) {
  const turns = groupByTurn(moves);

  return (
    <ol className="max-h-[28rem] overflow-y-auto text-sm">
      {turns.map(({ number, white, black }) => (
        <li
          key={number}
          className="grid grid-cols-[2.5rem_1fr_1fr] items-center gap-1 border-b border-slate-100 py-0.5 dark:border-slate-800"
        >
          <span className="pl-1 tabular-nums opacity-50">{number}.</span>
          <MoveButton move={white} currentPly={currentPly} onSelect={onSelectPly} />
          <MoveButton move={black} currentPly={currentPly} onSelect={onSelectPly} />
        </li>
      ))}
    </ol>
  );
}

function MoveButton({
  move,
  currentPly,
  onSelect,
}: {
  move: AnalyzedMoveOut | undefined;
  currentPly: number;
  onSelect: (ply: number) => void;
}) {
  if (!move) return <span />;
  const style = classificationStyle(move.classification);
  const isCurrent = move.ply === currentPly;

  return (
    <button
      type="button"
      onClick={() => onSelect(move.ply)}
      title={`${style.label} · precisión ${formatAccuracy(move.move_accuracy)}`}
      className={`flex items-center gap-1.5 rounded px-1.5 py-0.5 text-left hover:bg-slate-100 dark:hover:bg-slate-800 ${
        isCurrent ? "bg-indigo-100 font-medium dark:bg-indigo-900/60" : ""
      }`}
    >
      <span className="font-mono">{move.san}</span>
      <span className={`rounded px-1 text-[10px] leading-4 ${style.className}`}>{style.symbol}</span>
    </button>
  );
}

interface Turn {
  number: number;
  white?: AnalyzedMoveOut;
  black?: AnalyzedMoveOut;
}

/** El ply 0 es la primera jugada de las blancas, así que el número de turno
 * es `ply / 2 + 1` y la paridad decide de qué color es. */
function groupByTurn(moves: AnalyzedMoveOut[]): Turn[] {
  const turns: Turn[] = [];
  for (const move of moves) {
    const number = Math.floor(move.ply / 2) + 1;
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

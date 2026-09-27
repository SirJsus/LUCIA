/** Lista de jugadas con su clasificación (RF-5.1), emparejadas por turno.
 *
 * La rejilla de turnos es la compartida (`components/board/TurnList`), la
 * misma que usa la lista del sparring; lo propio de aquí es la celda: un botón
 * que navega a la jugada y enseña cómo la clasificó el análisis.
 *
 * `startingPly` es lo que hay que sumar al ply de cada jugada para llegar al
 * número que se lee en un tablero: en una partida que empieza en la jugada 12
 * (odds chess, Chess960, partidas desde posición) el ply 0 no es "1." Sale de
 * la posición de partida del PGN, en `lib/moves.ts`.
 */
import type { AnalyzedMoveOut } from "@lucia/shared-types";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { MoveButton } from "../../components/board/MoveButton";
import { TurnList } from "../../components/board/TurnList";
import { formatAccuracy } from "../../lib/format";
import { turnsOf } from "../../lib/moves";

interface MoveListProps {
  moves: AnalyzedMoveOut[];
  currentPly: number;
  startingPly: number;
  onSelectPly: (ply: number) => void;
}

export function MoveList({ moves, currentPly, startingPly, onSelectPly }: MoveListProps) {
  const turns = turnsOf(moves, (move) => move.ply + startingPly);

  return (
    <TurnList
      turns={turns}
      renderMove={(move) => (
        <AnalyzedMoveButton move={move} currentPly={currentPly} onSelect={onSelectPly} />
      )}
    />
  );
}

function AnalyzedMoveButton({
  move,
  currentPly,
  onSelect,
}: {
  move: AnalyzedMoveOut | null;
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

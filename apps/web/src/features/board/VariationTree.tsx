/** Árbol de variantes navegable (RF-6.3): la línea principal en línea, las
 * variantes indentadas, con acciones de promover y borrar. */
import { EmptyState } from "../../components/Feedback";
import { MoveButton } from "../../components/board/MoveButton";
import { MOVE_LIST_HEIGHT_CLASS } from "../../components/styles";
import { moveNumberLabel, plyFromFen } from "../../lib/moves";
import { type TreeNode } from "./tree";

interface VariationTreeProps {
  root: TreeNode;
  currentId: string;
  onSelect: (nodeId: string) => void;
  onPromote: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
}

export function VariationTree({
  root,
  currentId,
  onSelect,
  onPromote,
  onDelete,
}: VariationTreeProps) {
  if (root.children.length === 0) {
    return (
      <div className="p-3">
        <EmptyState title="Sin variantes todavía">
          Mueve una pieza en el tablero para empezar la variante.
        </EmptyState>
      </div>
    );
  }

  return (
    <div className={`${MOVE_LIST_HEIGHT_CLASS} overflow-y-auto p-2 text-sm`}>
      <Variation
        node={root}
        // El tablero puede arrancar de un FEN o de un PGN con `[SetUp "1"]`:
        // la numeración sale de la posición raíz, no de un 1. fijo, para que
        // coincida con la del PGN que exporta "Copiar PGN" (`toPgn`).
        ply={plyFromFen(root.fen)}
        currentId={currentId}
        onSelect={onSelect}
        onPromote={onPromote}
        onDelete={onDelete}
      />
    </div>
  );
}

function Variation({
  node,
  ply,
  currentId,
  onSelect,
  onPromote,
  onDelete,
  depth = 0,
}: {
  node: TreeNode;
  ply: number;
  currentId: string;
  onSelect: (id: string) => void;
  onPromote: (id: string) => void;
  onDelete: (id: string) => void;
  depth?: number;
}) {
  if (node.children.length === 0) return null;
  const [mainChild, ...variations] = node.children;

  return (
    <>
      <MoveChip
        node={mainChild}
        ply={ply}
        isCurrent={mainChild.id === currentId}
        onSelect={onSelect}
        onPromote={onPromote}
        onDelete={onDelete}
        canPromote={depth > 0}
      />

      {variations.map((variation) => (
        <div
          key={variation.id}
          className="my-1 border-l-2 border-slate-200 pl-2 opacity-90 dark:border-slate-700"
        >
          <MoveChip
            node={variation}
            ply={ply}
            isCurrent={variation.id === currentId}
            onSelect={onSelect}
            onPromote={onPromote}
            onDelete={onDelete}
            canPromote
          />
          <Variation
            node={variation}
            ply={ply + 1}
            currentId={currentId}
            onSelect={onSelect}
            onPromote={onPromote}
            onDelete={onDelete}
            depth={depth + 1}
          />
        </div>
      ))}

      <Variation
        node={mainChild}
        ply={ply + 1}
        currentId={currentId}
        onSelect={onSelect}
        onPromote={onPromote}
        onDelete={onDelete}
        depth={depth}
      />
    </>
  );
}

function MoveChip({
  node,
  ply,
  isCurrent,
  onSelect,
  onPromote,
  onDelete,
  canPromote,
}: {
  node: TreeNode;
  ply: number;
  isCurrent: boolean;
  onSelect: (id: string) => void;
  onPromote: (id: string) => void;
  onDelete: (id: string) => void;
  canPromote: boolean;
}) {
  return (
    <span className="group mr-1 inline-flex items-center gap-1">
      {ply % 2 === 0 && <span className="opacity-50">{moveNumberLabel(ply)}</span>}
      <MoveButton isCurrent={isCurrent} onClick={() => onSelect(node.id)} className="px-1">
        {node.san}
      </MoveButton>
      {/* Promover y borrar estaban solo en `group-hover`: sin ratón no había
          forma de llegar a ellas, y al tabular se caía en un botón invisible.
          Ahora están siempre, atenuadas, y se realzan al señalar o al enfocar
          (criterios C-1 y C-7 de docs/07-coherencia-ui.md). */}
      <span className="inline-flex gap-0.5 opacity-40 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        {canPromote && (
          <ChipAction
            onClick={() => onPromote(node.id)}
            accessibleName={`Convertir ${node.san} en línea principal`}
            symbol="▲"
          />
        )}
        <ChipAction
          onClick={() => onDelete(node.id)}
          accessibleName={`Eliminar ${node.san} y lo que sigue`}
          symbol="✕"
          className="hover:bg-red-100 dark:hover:bg-red-900/60"
        />
      </span>
    </span>
  );
}

function ChipAction({
  onClick,
  accessibleName,
  symbol,
  className = "hover:bg-slate-200 dark:hover:bg-slate-700",
}: {
  onClick: () => void;
  accessibleName: string;
  symbol: string;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={accessibleName}
      title={accessibleName}
      className={`rounded px-1 text-xs ${className}`}
    >
      {symbol}
    </button>
  );
}

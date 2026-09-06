/** Árbol de variantes navegable (RF-6.3): la línea principal en línea, las
 * variantes indentadas, con acciones de promover y borrar. */
import type { TreeNode } from "./tree";

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
      <p className="p-3 text-sm opacity-60">
        Mueve una pieza en el tablero para empezar la variante.
      </p>
    );
  }

  return (
    <div className="max-h-[26rem] overflow-y-auto p-2 text-sm">
      <Variation
        node={root}
        ply={0}
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
  const [principal, ...variantes] = node.children;

  return (
    <>
      <MoveChip
        node={principal}
        ply={ply}
        isCurrent={principal.id === currentId}
        onSelect={onSelect}
        onPromote={onPromote}
        onDelete={onDelete}
        canPromote={depth > 0}
      />

      {variantes.map((variante) => (
        <div
          key={variante.id}
          className="my-1 border-l-2 border-slate-200 pl-2 opacity-90 dark:border-slate-700"
        >
          <MoveChip
            node={variante}
            ply={ply}
            isCurrent={variante.id === currentId}
            onSelect={onSelect}
            onPromote={onPromote}
            onDelete={onDelete}
            canPromote
          />
          <Variation
            node={variante}
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
        node={principal}
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
      {ply % 2 === 0 && <span className="opacity-50">{Math.floor(ply / 2) + 1}.</span>}
      <button
        type="button"
        onClick={() => onSelect(node.id)}
        className={`rounded px-1 font-mono hover:bg-slate-100 dark:hover:bg-slate-800 ${
          isCurrent ? "bg-indigo-100 font-medium dark:bg-indigo-900/60" : ""
        }`}
      >
        {node.san}
      </button>
      <span className="hidden gap-0.5 group-hover:inline-flex">
        {canPromote && (
          <button
            type="button"
            onClick={() => onPromote(node.id)}
            title="Convertir en línea principal"
            className="rounded px-1 text-xs opacity-60 hover:bg-slate-200 hover:opacity-100 dark:hover:bg-slate-700"
          >
            ▲
          </button>
        )}
        <button
          type="button"
          onClick={() => onDelete(node.id)}
          title="Borrar esta jugada y lo que sigue"
          className="rounded px-1 text-xs opacity-60 hover:bg-red-100 hover:opacity-100 dark:hover:bg-red-900/60"
        >
          ✕
        </button>
      </span>
    </span>
  );
}

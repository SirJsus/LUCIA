/** Árbol de variantes de un tablero de análisis (RF-6.3).
 *
 * La API guarda esto como JSON opaco: la validación de jugadas vive aquí,
 * donde está chess.js, para no duplicar reglas de ajedrez en el servidor.
 *
 * El árbol tiene una raíz sin jugada (la posición de partida) y cada nodo
 * guarda la jugada que llevó hasta él. La "línea principal" es siempre el
 * primer hijo, así que promover una variante es moverla a la posición 0.
 */
import { Chess } from "chess.js";

export interface TreeNode {
  id: string;
  /** Jugada que llevó a este nodo. `null` solo en la raíz. */
  san: string | null;
  uci: string | null;
  /** FEN resultante. En la raíz es la posición de partida del tablero. */
  fen: string;
  comment?: string;
  children: TreeNode[];
}

export function createRoot(fen: string): TreeNode {
  return { id: "root", san: null, uci: null, fen, children: [] };
}

/** ¿El JSON que devolvió la API tiene forma de árbol? Un tablero guardado por
 * una versión anterior (o a mano) no debería tumbar la pantalla. */
export function isTreeNode(value: unknown): value is TreeNode {
  if (typeof value !== "object" || value === null) return false;
  const node = value as Partial<TreeNode>;
  return typeof node.id === "string" && typeof node.fen === "string" && Array.isArray(node.children);
}

function newId(): string {
  return Math.random().toString(36).slice(2, 10);
}

/** Copia superficial del camino hasta `targetId`, aplicando `transform` al
 * nodo encontrado. Devuelve `null` si el id no existe.
 *
 * Se copia en vez de mutar para que React vea un objeto nuevo y vuelva a
 * renderizar; mutar el árbol en sitio dejaría la pantalla desactualizada.
 */
function updateNode(
  node: TreeNode,
  targetId: string,
  transform: (found: TreeNode) => TreeNode,
): TreeNode | null {
  if (node.id === targetId) return transform(node);

  for (let index = 0; index < node.children.length; index++) {
    const updated = updateNode(node.children[index], targetId, transform);
    if (updated) {
      const children = [...node.children];
      children[index] = updated;
      return { ...node, children };
    }
  }
  return null;
}

export function findNode(node: TreeNode, targetId: string): TreeNode | null {
  if (node.id === targetId) return node;
  for (const child of node.children) {
    const found = findNode(child, targetId);
    if (found) return found;
  }
  return null;
}

/** Camino desde la raíz hasta un nodo, ambos incluidos. */
export function pathToNode(root: TreeNode, targetId: string): TreeNode[] {
  if (root.id === targetId) return [root];
  for (const child of root.children) {
    const sub = pathToNode(child, targetId);
    if (sub.length > 0) return [root, ...sub];
  }
  return [];
}

export interface AddMoveResult {
  root: TreeNode;
  /** Nodo donde queda el cursor: el nuevo, o el que ya existía. */
  nodeId: string;
  /** `true` si la jugada ya estaba en el árbol y solo se navegó hasta ella. */
  existed: boolean;
}

/** Añade una jugada como hija de `parentId`, o reutiliza la rama si ya existe.
 *
 * Reutilizar en vez de duplicar es importante: al repetir una línea conocida
 * el usuario espera continuar por ella, no crear una variante idéntica.
 * Devuelve `null` si la jugada es ilegal en esa posición.
 */
export function addMove(root: TreeNode, parentId: string, moveSan: string): AddMoveResult | null {
  const parent = findNode(root, parentId);
  if (!parent) return null;

  const chess = new Chess(parent.fen);
  let move;
  try {
    move = chess.move(moveSan);
  } catch {
    return null; // jugada ilegal en esta posición
  }
  if (!move) return null;

  const existing = parent.children.find((child) => child.uci === move.lan);
  if (existing) return { root, nodeId: existing.id, existed: true };

  const child: TreeNode = {
    id: newId(),
    san: move.san,
    uci: move.lan,
    fen: move.after,
    children: [],
  };
  const updated = updateNode(root, parentId, (found) => ({
    ...found,
    children: [...found.children, child],
  }));
  return updated ? { root: updated, nodeId: child.id, existed: false } : null;
}

/** Borra un nodo y todo lo que cuelga de él. La raíz no se puede borrar. */
export function deleteNode(root: TreeNode, targetId: string): TreeNode {
  if (targetId === root.id) return root;
  return removeChild(root, targetId);
}

function removeChild(node: TreeNode, targetId: string): TreeNode {
  if (node.children.some((child) => child.id === targetId)) {
    return { ...node, children: node.children.filter((child) => child.id !== targetId) };
  }
  return { ...node, children: node.children.map((child) => removeChild(child, targetId)) };
}

/** Convierte una variante en línea principal moviéndola al primer lugar entre
 * sus hermanas (RF-6.3). */
export function promoteNode(root: TreeNode, targetId: string): TreeNode {
  if (root.id === targetId) return root; // la raíz no tiene hermanas
  return promoteIn(root, targetId);
}

function promoteIn(node: TreeNode, targetId: string): TreeNode {
  const index = node.children.findIndex((child) => child.id === targetId);
  if (index > 0) {
    const children = [...node.children];
    const [promoted] = children.splice(index, 1);
    return { ...node, children: [promoted, ...children] };
  }
  return { ...node, children: node.children.map((child) => promoteIn(child, targetId)) };
}

/** La línea principal: seguir siempre el primer hijo desde la raíz. */
export function mainLine(root: TreeNode): TreeNode[] {
  const line: TreeNode[] = [];
  let current = root;
  while (current.children.length > 0) {
    current = current.children[0];
    line.push(current);
  }
  return line;
}

/** Exporta el árbol a PGN con variantes entre paréntesis (RF-6.7). */
export function toPgn(root: TreeNode): string {
  const movetext = renderVariation(root, plyOf(root.fen));
  const setup =
    root.fen === new Chess().fen() ? "" : `[SetUp "1"]\n[FEN "${root.fen}"]\n\n`;
  return `${setup}${movetext.trim()} *\n`;
}

function plyOf(fen: string): number {
  // Del FEN salen el número de jugada y el turno, que dan el ply inicial.
  const fenFields = fen.split(" ");
  const fullmove = Number(fenFields[5] ?? 1);
  const sideToMove = fenFields[1] ?? "w";
  return (fullmove - 1) * 2 + (sideToMove === "b" ? 1 : 0);
}

function renderVariation(node: TreeNode, ply: number): string {
  if (node.children.length === 0) return "";

  const [mainChild, ...variations] = node.children;
  let movetext = `${moveNumber(ply)}${mainChild.san}`;
  if (mainChild.comment) movetext += ` {${mainChild.comment}}`;

  for (const variation of variations) {
    let sub = `${moveNumber(ply)}${variation.san}`;
    if (variation.comment) sub += ` {${variation.comment}}`;
    const variationContinuation = renderVariation(variation, ply + 1);
    movetext += ` (${sub}${variationContinuation ? ` ${variationContinuation}` : ""})`;
  }

  const mainContinuation = renderVariation(mainChild, ply + 1);
  return mainContinuation ? `${movetext} ${mainContinuation}` : movetext;
}

function moveNumber(ply: number): string {
  const fullmoveNumber = Math.floor(ply / 2) + 1;
  return ply % 2 === 0 ? `${fullmoveNumber}. ` : `${fullmoveNumber}... `;
}

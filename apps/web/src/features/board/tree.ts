/** Árbol de variantes de un tablero de análisis (RF-6.3).
 *
 * La API guarda esto como JSON opaco: la validación de jugadas vive aquí,
 * donde está chess.js, para no duplicar reglas de ajedrez en el servidor.
 *
 * El árbol tiene una raíz sin jugada (la posición de partida) y cada nodo
 * guarda la jugada que llevó hasta él. La "línea principal" es siempre el
 * primer hijo, así que promover una variante es moverla a la posición 0.
 */
import type { AnalyzedMoveOut } from "@lucia/shared-types";
import { Chess } from "chess.js";
import { moveNumberLabel, plyFromFen } from "../../lib/moves";
import { STANDARD_STARTING_FEN } from "./position";

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

  const childResult = findOrCreateChild(parent, moveSan);
  if (!childResult) return null;
  if (childResult.existed) return { root, nodeId: childResult.child.id, existed: true };

  const updated = updateNode(root, parentId, (found) => ({
    ...found,
    children: [...found.children, childResult.child],
  }));
  return updated ? { root: updated, nodeId: childResult.child.id, existed: false } : null;
}

/** El hijo de `parent` que corresponde a esa jugada: el que ya estaba en el
 * árbol o uno nuevo todavía sin colgar. `null` si la jugada es ilegal en esa
 * posición.
 *
 * No toca `parent`: quien llama decide cómo cuelga el hijo nuevo, copiando el
 * camino (`addMove`, para que React vea un árbol nuevo) o mutando
 * (`parseVariation`, sobre un árbol que todavía no ha visto nadie).
 */
function findOrCreateChild(
  parent: TreeNode,
  san: string,
): { child: TreeNode; existed: boolean } | null {
  let move;
  try {
    move = new Chess(parent.fen).move(san);
  } catch {
    return null; // jugada ilegal en esta posición
  }
  if (!move) return null;

  const existing = parent.children.find((child) => child.uci === move.lan);
  if (existing) return { child: existing, existed: true };

  return {
    child: { id: newId(), san: move.san, uci: move.lan, fen: move.after, children: [] },
    existed: false,
  };
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

/** Empareja las jugadas de un análisis con los nodos de la línea principal
 * (RF-6.9).
 *
 * Se emparejan por posición mientras coincida la jugada, no por `ply` a
 * secas: el tablero se sigue editando después de analizarlo, y pegar una
 * clasificación sobre una jugada distinta de la que se analizó sería enseñar
 * un dato falso con toda la apariencia de verdadero. Lo que quede sin
 * emparejar es lo que la pantalla avisa.
 */
export function matchAnalyzedLine(mainLineNodes: TreeNode[], analyzedMoves: AnalyzedMoveOut[]) {
  const analyzedByNodeId = new Map<string, AnalyzedMoveOut>();
  let matched = 0;
  while (
    matched < Math.min(mainLineNodes.length, analyzedMoves.length) &&
    mainLineNodes[matched].san === analyzedMoves[matched].san
  ) {
    analyzedByNodeId.set(mainLineNodes[matched].id, analyzedMoves[matched]);
    matched++;
  }
  return {
    analyzedByNodeId,
    /** Alguna jugada analizada ya no está donde estaba: el análisis es de
     * otro tablero, aunque sea el mismo archivo. */
    hasChangedSinceAnalysis: matched < analyzedMoves.length,
    movesAddedSinceAnalysis: analyzedMoves.length > 0 ? mainLineNodes.length - matched : 0,
  };
}

/** Exporta el árbol a PGN con variantes entre paréntesis (RF-6.7). */
export function toPgn(root: TreeNode): string {
  const movetext = renderVariation(root, plyFromFen(root.fen));
  const setup =
    root.fen === STANDARD_STARTING_FEN ? "" : `[SetUp "1"]\n[FEN "${root.fen}"]\n\n`;
  return `${setup}${movetext.trim()} *\n`;
}

function renderVariation(node: TreeNode, ply: number): string {
  if (node.children.length === 0) return "";

  const [mainChild, ...variations] = node.children;
  let movetext = `${moveNumberLabel(ply)} ${mainChild.san}`;
  if (mainChild.comment) movetext += ` {${mainChild.comment}}`;

  for (const variation of variations) {
    let sub = `${moveNumberLabel(ply)} ${variation.san}`;
    if (variation.comment) sub += ` {${variation.comment}}`;
    const variationContinuation = renderVariation(variation, ply + 1);
    movetext += ` (${sub}${variationContinuation ? ` ${variationContinuation}` : ""})`;
  }

  const mainContinuation = renderVariation(mainChild, ply + 1);
  return mainContinuation ? `${movetext} ${mainContinuation}` : movetext;
}

/** Lo que trae un PGN leído (RF-6.7). */
export interface ParsedPgn {
  root: TreeNode;
  /** Cabeceras `[Clave "valor"]` tal cual venían; de `White`, `Black` y
   * `Date` sale el título del tablero importado. */
  headers: Record<string, string>;
  /** Cuántas ramas se cortaron por una jugada que no encajaba. Sale a la
   * pantalla: una importación a medias anunciada como completa deja al
   * usuario con una partida truncada y sin saberlo. */
  truncatedBranches: number;
}

/** Qué se descarta del movetext sin mirarlo: número de jugada ("12." o
 * "12..."), NAG ("$4") y resultado. No aportan nada al árbol —el número se
 * deduce del ply y el símbolo de la jugada, de su clasificación— y colarlos
 * como SAN los haría pasar por jugadas ilegales. */
const IGNORED_MOVETEXT_TOKEN = /^(\d+\.(\.\.)?|\$\d+|1-0|0-1|1\/2-1\/2|\*)$/;

/** Signos de apreciación pegados a la jugada ("Cf3?!", "Dxh7!"). El árbol
 * guarda la jugada, no el juicio: la clasificación la pone el análisis
 * (RF-2.2) y chess.js rechazaría el SAN con el signo dentro. */
const ANNOTATION_SUFFIX = /[!?]+$/;

/** Lee un PGN con variantes y comentarios y lo convierte en árbol (RF-6.7).
 *
 * Es la operación inversa de `toPgn`, y la que permite traer una partida de
 * lichess, ChessBase o SCID —o una propia ya anotada (RF-5.5)— al tablero de
 * análisis. Vive aquí y no en la API por la misma razón que el resto del
 * módulo: quien sabe si una jugada es legal es chess.js.
 *
 * **Lanza** un `Error` con el motivo cuando el texto no da un árbol: quien
 * llama lo hace desde una mutación y ya enseña el mensaje, y distinguir "no
 * hay jugadas" de "la posición de partida es ilegal" importa, porque la
 * respuesta del usuario a cada una es distinta.
 *
 * Una jugada suelta ilegal a mitad de una variante **no** tumba la lectura:
 * corta esa rama, cuenta el corte en `truncatedBranches` y sigue. Rechazar un
 * archivo de trescientas jugadas por un error de transcripción sería peor;
 * callar el recorte, también.
 */
export function fromPgn(pgn: string): ParsedPgn {
  const { headers, movetext } = splitHeadersAndMovetext(pgn);
  const startFen = headers.FEN ?? STANDARD_STARTING_FEN;
  try {
    new Chess(startFen);
  } catch {
    throw new Error('La cabecera [FEN "…"] no describe una posición legal.');
  }

  const root = createRoot(startFen);
  const truncatedBranches = parseVariation(tokenizeMovetext(movetext), 0, root).truncatedBranches;
  if (mainLine(root).length === 0) {
    throw new Error("Ese texto no tiene ninguna jugada legal que importar.");
  }
  return { root, headers, truncatedBranches };
}

/** Separa las cabeceras `[Clave "valor"]` del movetext. */
function splitHeadersAndMovetext(pgn: string): {
  headers: Record<string, string>;
  movetext: string;
} {
  const headers: Record<string, string> = {};
  const movetextLines: string[] = [];
  for (const line of pgn.split("\n")) {
    const header = line.trim().match(/^\[(\w+)\s+"(.*)"\]$/);
    if (header) headers[header[1]] = header[2];
    else movetextLines.push(line);
  }
  return { headers, movetext: movetextLines.join("\n") };
}

type PgnToken =
  | { kind: "move"; san: string }
  | { kind: "comment"; text: string }
  | { kind: "variationStart" }
  | { kind: "variationEnd" };

/** Parte el movetext en jugadas, comentarios y paréntesis de variante.
 *
 * Se recorre carácter a carácter y no con una expresión regular porque los
 * comentarios pueden contener paréntesis —"{mejor era (12. Cf3)}" es un
 * comentario válido— y cualquier partición por símbolos los rompería.
 */
function tokenizeMovetext(movetext: string): PgnToken[] {
  const tokens: PgnToken[] = [];
  let word = "";

  const endWord = () => {
    if (word && !IGNORED_MOVETEXT_TOKEN.test(word)) tokens.push({ kind: "move", san: word });
    word = "";
  };

  for (let index = 0; index < movetext.length; index++) {
    const character = movetext[index];
    // Las dos formas de comentario del estándar: entre llaves o desde ";"
    // hasta el fin de línea.
    if (character === "{" || character === ";") {
      endWord();
      const terminator = movetext.indexOf(character === "{" ? "}" : "\n", index);
      const close = terminator === -1 ? movetext.length : terminator;
      tokens.push({ kind: "comment", text: movetext.slice(index + 1, close).trim() });
      index = close;
    } else if (character === "(" || character === ")") {
      endWord();
      tokens.push({ kind: character === "(" ? "variationStart" : "variationEnd" });
    } else if (/\s/.test(character)) {
      endWord();
    } else {
      word += character;
    }
  }
  endWord();
  return tokens;
}

/** Cuelga de `parent` las jugadas de una variante y devuelve dónde se quedó.
 *
 * El árbol se construye **mutando** los hijos, al revés que el resto del
 * módulo: mientras se lee, el árbol todavía no lo ha visto nadie, así que no
 * hay render que invalidar y copiar el camino en cada jugada convertiría una
 * partida larga en un trabajo cuadrático.
 */
function parseVariation(
  tokens: PgnToken[],
  start: number,
  parent: TreeNode,
): { index: number; truncatedBranches: number } {
  // La variante que abre un paréntesis es hermana de la última jugada leída,
  // no hija: cuelga de la posición **anterior** a ella.
  let previous = parent;
  let current = parent;
  let index = start;
  let truncatedBranches = 0;

  while (index < tokens.length) {
    const token = tokens[index];
    index++;
    if (token.kind === "variationEnd") return { index, truncatedBranches };
    if (token.kind === "variationStart") {
      const variation = parseVariation(tokens, index, previous);
      index = variation.index;
      truncatedBranches += variation.truncatedBranches;
    } else if (token.kind === "comment") {
      if (current !== parent && token.text) current.comment = token.text;
    } else {
      const childResult = findOrCreateChild(current, token.san.replace(ANNOTATION_SUFFIX, ""));
      if (!childResult) {
        const skipped = skipToVariationEnd(tokens, index);
        return {
          index: skipped.index,
          // Esta rama más las que colgaban de lo saltado.
          truncatedBranches: truncatedBranches + 1 + skipped.skippedVariations,
        };
      }
      if (!childResult.existed) current.children.push(childResult.child);
      previous = current;
      current = childResult.child;
    }
  }
  return { index, truncatedBranches };
}

/** Salta hasta cerrar la variante en curso, tras una jugada ilegal: lo que
 * sigue se apoyaba en ella y ya no encaja en ninguna posición. */
function skipToVariationEnd(
  tokens: PgnToken[],
  start: number,
): { index: number; skippedVariations: number } {
  let depth = 0;
  let skippedVariations = 0;
  for (let index = start; index < tokens.length; index++) {
    if (tokens[index].kind === "variationStart") {
      depth++;
      // Cada paréntesis de dentro es otra rama que se pierde con el salto:
      // sin contarla, el aviso diría "se cortó 1 rama" tras perder tres.
      skippedVariations++;
    } else if (tokens[index].kind === "variationEnd") {
      if (depth === 0) return { index: index + 1, skippedVariations };
      depth--;
    }
  }
  return { index: tokens.length, skippedVariations };
}

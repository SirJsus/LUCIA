import { Chess } from "chess.js";
import { describe, expect, it } from "vitest";
import {
  addMove,
  createRoot,
  deleteNode,
  findNode,
  isTreeNode,
  mainLine,
  pathToNode,
  promoteNode,
  toPgn,
} from "../tree";

const START = new Chess().fen();

/** Aplica una secuencia de jugadas en línea recta desde la raíz. */
function lineFrom(fen: string, moves: string[]) {
  let root = createRoot(fen);
  let cursor = root.id;
  for (const san of moves) {
    const result = addMove(root, cursor, san);
    if (!result) throw new Error(`jugada rechazada: ${san}`);
    root = result.root;
    cursor = result.nodeId;
  }
  return { root, cursor };
}

describe("addMove", () => {
  it("añade una jugada legal", () => {
    const result = addMove(createRoot(START), "root", "e4");
    expect(result).not.toBeNull();
    expect(result!.existed).toBe(false);
    expect(mainLine(result!.root).map((n) => n.san)).toEqual(["e4"]);
  });

  it("rechaza una jugada ilegal en vez de corromper el árbol", () => {
    expect(addMove(createRoot(START), "root", "e5")).toBeNull();
    expect(addMove(createRoot(START), "root", "Qh5xh7")).toBeNull();
  });

  it("reutiliza la rama si la jugada ya existe, en vez de duplicarla", () => {
    const { root } = lineFrom(START, ["e4"]);
    const repeatedResult = addMove(root, "root", "e4");

    expect(repeatedResult!.existed).toBe(true);
    expect(repeatedResult!.root.children).toHaveLength(1);
  });

  it("crea una variante cuando la jugada es distinta", () => {
    const { root } = lineFrom(START, ["e4"]);
    const rootWithVariation = addMove(root, "root", "d4")!.root;

    expect(rootWithVariation.children.map((c) => c.san)).toEqual(["e4", "d4"]);
  });

  it("devuelve null si el nodo padre no existe", () => {
    expect(addMove(createRoot(START), "no-existe", "e4")).toBeNull();
  });

  it("no muta el árbol original (React necesita objetos nuevos)", () => {
    const root = createRoot(START);
    addMove(root, "root", "e4");
    expect(root.children).toHaveLength(0);
  });
});

describe("promoteNode", () => {
  it("convierte una variante en línea principal", () => {
    const { root } = lineFrom(START, ["e4"]);
    const addedVariation = addMove(root, "root", "d4")!;
    expect(mainLine(addedVariation.root)[0].san).toBe("e4");

    const rootAfterPromote = promoteNode(addedVariation.root, addedVariation.nodeId);
    expect(mainLine(rootAfterPromote)[0].san).toBe("d4");
  });

  it("promover la raíz no cambia nada", () => {
    const root = createRoot(START);
    expect(promoteNode(root, "root")).toBe(root);
  });
});

describe("deleteNode", () => {
  it("borra el nodo y todo lo que cuelga de él", () => {
    const { root, cursor } = lineFrom(START, ["e4", "e5", "Nf3"]);
    const e5Node = pathToNode(root, cursor)[2];

    const rootAfterDelete = deleteNode(root, e5Node.id);

    expect(mainLine(rootAfterDelete).map((n) => n.san)).toEqual(["e4"]);
    expect(findNode(rootAfterDelete, cursor)).toBeNull();
  });

  it("no permite borrar la raíz", () => {
    const root = createRoot(START);
    expect(deleteNode(root, "root")).toBe(root);
  });
});

describe("pathToNode", () => {
  it("devuelve el camino desde la raíz, ambos incluidos", () => {
    const { root, cursor } = lineFrom(START, ["e4", "e5"]);
    const path = pathToNode(root, cursor);

    expect(path.map((n) => n.san)).toEqual([null, "e4", "e5"]);
  });

  it("devuelve vacío si el nodo no existe", () => {
    expect(pathToNode(createRoot(START), "fantasma")).toEqual([]);
  });
});

describe("toPgn", () => {
  it("exporta la línea principal con numeración correcta", () => {
    const { root } = lineFrom(START, ["e4", "e5", "Nf3"]);
    expect(toPgn(root)).toContain("1. e4 1... e5 2. Nf3");
  });

  it("mete las variantes entre paréntesis", () => {
    const { root } = lineFrom(START, ["e4"]);
    const rootWithVariation = addMove(root, "root", "d4")!.root;

    expect(toPgn(rootWithVariation)).toContain("(1. d4)");
  });

  it("añade la cabecera FEN cuando no arranca de la posición inicial", () => {
    const fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3";
    const pgn = toPgn(createRoot(fen));

    expect(pgn).toContain('[SetUp "1"]');
    expect(pgn).toContain(fen);
  });

  it("numera bien cuando la posición de partida es de negras", () => {
    const fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1";
    const { root } = lineFrom(fen, ["e5"]);
    expect(toPgn(root)).toContain("1... e5");
  });
});

describe("isTreeNode", () => {
  it("acepta un árbol bien formado y rechaza basura", () => {
    expect(isTreeNode(createRoot(START))).toBe(true);
    expect(isTreeNode({})).toBe(false);
    expect(isTreeNode(null)).toBe(false);
    expect(isTreeNode({ id: "x", fen: "y" })).toBe(false); // sin children
  });
});

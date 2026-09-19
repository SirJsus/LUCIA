import { Chess } from "chess.js";
import { describe, expect, it } from "vitest";
import {
  addMove,
  createRoot,
  deleteNode,
  findNode,
  isTreeNode,
  mainLine,
  matchAnalyzedLine,
  pathToNode,
  promoteNode,
  toPgn,
  fromPgn,
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

describe("matchAnalyzedLine", () => {
  /** De un análisis solo importa aquí el `san`. */
  const analyzed = (sans: string[]) =>
    sans.map((san) => ({ san }) as Parameters<typeof matchAnalyzedLine>[1][number]);

  it("empareja las jugadas que siguen donde estaban", () => {
    const line = mainLine(lineFrom(START, ["e4", "e5", "Nf3"]).root);
    const result = matchAnalyzedLine(line, analyzed(["e4", "e5", "Nf3"]));
    expect([...result.analyzedByNodeId.keys()]).toEqual(line.map((n) => n.id));
    expect(result.hasChangedSinceAnalysis).toBe(false);
    expect(result.movesAddedSinceAnalysis).toBe(0);
  });

  it("corta en la primera jugada que ya no coincide y lo avisa", () => {
    const line = mainLine(lineFrom(START, ["e4", "c5"]).root);
    const result = matchAnalyzedLine(line, analyzed(["e4", "e5", "Nf3"]));
    expect(result.analyzedByNodeId.size).toBe(1);
    expect(result.hasChangedSinceAnalysis).toBe(true);
  });

  it("cuenta las jugadas añadidas después del análisis", () => {
    const line = mainLine(lineFrom(START, ["e4", "e5", "Nf3"]).root);
    const result = matchAnalyzedLine(line, analyzed(["e4"]));
    expect(result.hasChangedSinceAnalysis).toBe(false);
    expect(result.movesAddedSinceAnalysis).toBe(2);
  });

  it("sin análisis no hay nada que avisar", () => {
    const line = mainLine(lineFrom(START, ["e4"]).root);
    const result = matchAnalyzedLine(line, []);
    expect(result.hasChangedSinceAnalysis).toBe(false);
    expect(result.movesAddedSinceAnalysis).toBe(0);
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

describe("fromPgn", () => {
  it("lee la línea principal", () => {
    const parsed = fromPgn("1. e4 e5 2. Nf3 Nc6 *");
    expect(mainLine(parsed.root).map((node) => node.san)).toEqual(["e4", "e5", "Nf3", "Nc6"]);
  });

  it("cuelga la variante de la posición anterior a la jugada, no de ella", () => {
    // 1... c5 es hermana de 1... e5: las dos se juegan tras 1. e4.
    const parsed = fromPgn("1. e4 e5 (1... c5 2. Nf3) 2. Nf3 *");
    const afterE4 = parsed.root.children[0];

    expect(afterE4.children.map((node) => node.san)).toEqual(["e5", "c5"]);
    expect(afterE4.children[1].children.map((node) => node.san)).toEqual(["Nf3"]);
  });

  it("anida variantes dentro de variantes", () => {
    const parsed = fromPgn("1. e4 e5 (1... c5 2. Nf3 d6 (2... Nc6 3. d4)) *")!;
    const sicilian = parsed.root.children[0].children[1];
    const afterNf3 = sicilian.children[0];

    expect(afterNf3.children.map((node) => node.san)).toEqual(["d6", "Nc6"]);
  });

  it("guarda los comentarios en la jugada que comentan", () => {
    const parsed = fromPgn("1. e4 {La más jugada} e5 *");
    expect(parsed.root.children[0].comment).toBe("La más jugada");
    expect(parsed.root.children[0].children[0].comment).toBeUndefined();
  });

  it("no parte el comentario que lleva paréntesis dentro", () => {
    // Un comentario con "(" no puede abrir una variante.
    const parsed = fromPgn("1. e4 {mejor era (1. d4)} e5 *");
    expect(parsed.root.children[0].comment).toBe("mejor era (1. d4)");
    expect(parsed.root.children).toHaveLength(1);
  });

  it("descarta números de jugada, NAG y resultado", () => {
    const parsed = fromPgn("1. e4 $1 e5 $14 2. Nf3 1-0");
    expect(mainLine(parsed.root).map((node) => node.san)).toEqual(["e4", "e5", "Nf3"]);
  });

  it("acepta la jugada con su signo de apreciación pegado", () => {
    // El árbol guarda la jugada; el juicio lo pone el análisis.
    const parsed = fromPgn("1. e4! e5?! 2. Nf3?? *");
    expect(mainLine(parsed.root).map((node) => node.san)).toEqual(["e4", "e5", "Nf3"]);
  });

  it("arranca de la posición de la cabecera FEN", () => {
    const fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1";
    const parsed = fromPgn(`[SetUp "1"]\n[FEN "${fen}"]\n\n1... e5 *`);

    expect(parsed.root.fen).toBe(fen);
    expect(mainLine(parsed.root).map((node) => node.san)).toEqual(["e5"]);
  });

  it("devuelve las cabeceras, que son de donde sale el título propuesto", () => {
    const parsed = fromPgn('[White "Ana"]\n[Black "Beto"]\n\n1. e4 *');
    expect(parsed.headers.White).toBe("Ana");
  });

  it("corta la rama donde aparece una jugada ilegal y conserva el resto", () => {
    // Más útil que rechazar una partida entera por un error de transcripción.
    const parsed = fromPgn("1. e4 e5 (1... Qh4 2. Nf3) 2. Nf3 *");
    const afterE4 = parsed.root.children[0];

    expect(afterE4.children.map((node) => node.san)).toEqual(["e5"]);
    expect(mainLine(parsed.root).map((node) => node.san)).toEqual(["e4", "e5", "Nf3"]);
  });

  it("dice por qué no hay árbol, que no es lo mismo en los dos casos", () => {
    // El usuario hace cosas distintas ante "no hay jugadas" y ante "la
    // posición de partida es ilegal".
    expect(() => fromPgn('[White "Ana"]\n\n*')).toThrow(/jugada legal/);
    expect(() => fromPgn("esto no es un PGN")).toThrow(/jugada legal/);
    expect(() => fromPgn('[FEN "no es un fen"]\n\n1. e4 *')).toThrow(/posición legal/);
  });

  it("cuenta también las subvariantes que se pierden con la rama cortada", () => {
    // Al saltar tras 1... Qh4 (ilegal) se pierden dos ramas, no una.
    const parsed = fromPgn("1. e4 e5 (1... Qh4 (2. Nf3 d5) 2. Nf3) 2. Nf3 *");
    expect(parsed.truncatedBranches).toBe(2);
  });

  it("cuenta las ramas que corta, para que la pantalla lo diga", () => {
    const parsed = fromPgn("1. e4 e5 (1... Qh4 2. Nf3) 2. Nf3 *");
    expect(parsed.truncatedBranches).toBe(1);
    expect(fromPgn("1. e4 e5 *").truncatedBranches).toBe(0);
  });

  it("lee el PGN anotado que exporta la propia aplicación (RF-5.5)", () => {
    // Copiado tal cual de lo que emite `services/pgn_export.py`: NAG como
    // "$4", comentarios con espacios y paréntesis dentro, y salto de línea a
    // mitad del movetext. Es el PGN con el que "Abrir como tablero" (RF-6.6)
    // trae una partida ya analizada.
    const exported = [
      '[Event "?"]',
      '[Result "*"]',
      "",
      "1. e4 { Mejor jugada. 52 % de probabilidad de victoria (blancas) } 1... e5 $4",
      "{ Blunder. 31 % } ( 1... c5 { El motor prefería } ) *",
    ].join("\n");

    const parsed = fromPgn(exported);
    const afterE4 = parsed.root.children[0];

    expect(afterE4.comment).toBe("Mejor jugada. 52 % de probabilidad de victoria (blancas)");
    expect(afterE4.children.map((node) => node.san)).toEqual(["e5", "c5"]);
    expect(afterE4.children[0].comment).toBe("Blunder. 31 %");
    expect(afterE4.children[1].comment).toBe("El motor prefería");
  });

  it("conserva las variantes, que es lo que loadPgn de chess.js tira", () => {
    // Es la razón de existir del lector propio, y por la que las dos puertas
    // de la aplicación (crear tablero y panel de importar) pasan por aquí:
    // el mismo archivo no puede dar dos tableros distintos.
    const withVariation = "1. e4 e5 (1... c5 {Siciliana} 2. Nf3) 2. Nf3 *";
    const parsed = fromPgn(withVariation);

    const chessJs = new Chess();
    chessJs.loadPgn(withVariation);
    expect(chessJs.history()).toEqual(["e4", "e5", "Nf3"]); // la variante se perdió

    expect(parsed.root.children[0].children.map((node) => node.san)).toEqual(["e5", "c5"]);
  });

  it("sobrevive a la ida y vuelta por toPgn", () => {
    const original = "1. e4 e5 (1... c5 {Siciliana} 2. Nf3) 2. Nf3 Nc6 *";
    const once = fromPgn(original);
    const twice = fromPgn(toPgn(once.root));

    expect(toPgn(twice.root)).toBe(toPgn(once.root));
    expect(mainLine(twice.root).map((node) => node.san)).toEqual(["e4", "e5", "Nf3", "Nc6"]);
    expect(twice.root.children[0].children[1].comment).toBe("Siciliana");
  });
});

import { describe, expect, it } from "vitest";
import { arrowsFromEngineLines, arrowsFromPreviewLine, buildBoardConfig } from "../boardConfig";

/** Una línea del motor con lo mínimo que miran estas funciones. */
function engineLine(rank: number, scoreCp: number, ...pvUci: string[]) {
  return { rank, score_cp: scoreCp, score_mate: null, pv_uci: pvUci, pv_san: [] };
}

const BASE = { fen: "8/8/8/8/8/8/8/8 w - - 0 1", orientation: "white" as const };

describe("buildBoardConfig", () => {
  it("no manda 'movable' cuando el tablero es de solo lectura", () => {
    // chessground fusiona con deepMerge, que hace base[k] = nuevo[k] sin
    // comprobar: mandar `movable: undefined` le borra el estado interno y la
    // siguiente actualización falla con "Cannot set properties of undefined
    // (setting 'dests')". Este era el fallo del visor de partidas.
    const config = buildBoardConfig(BASE);

    expect("movable" in config).toBe(false);
    expect("turnColor" in config).toBe(false);
  });

  it("manda 'movable' con los destinos cuando el tablero es interactivo", () => {
    const dests = new Map([["e2", ["e3", "e4"]]]);
    const config = buildBoardConfig({ ...BASE, legalMoves: dests, turnColor: "black" });

    expect(config.movable?.dests).toBe(dests);
    expect(config.movable?.free).toBe(false);
    expect(config.movable?.color).toBe("black");
    expect(config.turnColor).toBe("black");
  });

  it("ninguna clave de primer nivel va en undefined, salvo lastMove", () => {
    // `lastMove` es la excepción: chessground lo trata aparte y es lo que
    // limpia el resaltado al volver a la posición inicial.
    const config = buildBoardConfig(BASE) as Record<string, unknown>;

    const undefinedKeys = Object.keys(config).filter((k) => config[k] === undefined);
    expect(undefinedKeys).toEqual(["lastMove"]);
  });

  it("resalta la última jugada y la limpia cuando no hay", () => {
    expect(buildBoardConfig({ ...BASE, lastMoveUci: "e2e4" }).lastMove).toEqual(["e2", "e4"]);
    expect(buildBoardConfig(BASE).lastMove).toBeUndefined();
  });

  it("convierte las flechas del motor en formas de chessground, o ninguna", () => {
    const config = buildBoardConfig({
      ...BASE,
      engineArrows: [
        { uci: "g1f3", brush: "green", label: "+0.35" },
        { uci: "e2e4", brush: "paleGreen" },
      ],
    });

    expect(config.drawable?.autoShapes).toEqual([
      { orig: "g1", dest: "f3", brush: "green", label: { text: "+0.35" } },
      { orig: "e2", dest: "e4", brush: "paleGreen" },
    ]);
    expect(buildBoardConfig(BASE).drawable?.autoShapes).toEqual([]);
  });

  it("recorta bien la promoción en el UCI de cuatro o cinco caracteres", () => {
    expect(buildBoardConfig({ ...BASE, lastMoveUci: "e7e8q" }).lastMove).toEqual(["e7", "e8"]);
  });
});

/** Copia literal del `deepMerge` de chessground (src/config.ts): hace
 * `base[k] = nuevo[k]` sin comprobar si el valor es `undefined`. */
type Mutable = Record<string, unknown>;

function deepMergeLikeChessground(base: Mutable, extend: Mutable): void {
  for (const key in extend) {
    if (key === "__proto__" || key === "constructor" || !Object.prototype.hasOwnProperty.call(extend, key))
      continue;
    if (
      Object.prototype.hasOwnProperty.call(base, key) &&
      isPlainObject(base[key]) &&
      isPlainObject(extend[key])
    )
      deepMergeLikeChessground(base[key] as Mutable, extend[key] as Mutable);
    else base[key] = extend[key];
  }
}

function isPlainObject(o: unknown): boolean {
  if (typeof o !== "object" || o === null) return false;
  const proto = Object.getPrototypeOf(o);
  return proto === Object.prototype || proto === null;
}

describe("compatibilidad con el merge real de chessground", () => {
  it("actualizar un tablero de solo lectura no le borra el estado interno", () => {
    // Estado como el que crea chessground al construirse.
    const state: Mutable = {
      movable: { free: false, showDests: true, events: {}, rookCastle: true },
      turnColor: "white",
    };

    // Varias actualizaciones seguidas, como al navegar por la partida.
    for (const lastMoveUci of [null, "e2e4", "e7e5", null]) {
      deepMergeLikeChessground(state, buildBoardConfig({ ...BASE, lastMoveUci }) as Mutable);
    }

    // Antes del arreglo, `movable` acababa en undefined y la siguiente
    // llamada fallaba al escribir `state.movable.dests`.
    expect(state.movable).toBeDefined();
    expect((state.movable as Mutable).rookCastle).toBe(true);
    expect(state.turnColor).toBe("white");
  });

  it("el tablero interactivo sí reemplaza los destinos, sin romper el resto", () => {
    const state: Mutable = {
      movable: { free: false, showDests: true, events: { after: () => {} }, rookCastle: true },
      turnColor: "white",
    };

    deepMergeLikeChessground(
      state,
      buildBoardConfig({
        ...BASE,
        legalMoves: new Map([["e2", ["e4"]]]),
        turnColor: "black",
      }) as Mutable,
    );

    const movable = state.movable as { dests: Map<string, string[]>; events: Mutable };
    expect(movable.dests.get("e2")).toEqual(["e4"]);
    expect(movable.events.after).toBeTypeOf("function"); // no se pierde
    expect(state.turnColor).toBe("black");
  });
});


describe("arrowsFromEngineLines", () => {
  it("destaca la mejor línea y atenúa las siguientes, con su evaluación encima", () => {
    const arrows = arrowsFromEngineLines([
      engineLine(1, 35, "g1f3", "d7d5"),
      engineLine(2, 10, "e2e4"),
      engineLine(3, -20, "d2d4"),
    ]);

    expect(arrows).toEqual([
      { uci: "g1f3", brush: "green", label: "+0.35" },
      { uci: "e2e4", brush: "paleGreen", label: "+0.10" },
      { uci: "d2d4", brush: "paleGrey", label: "−0.20" },
    ]);
  });

  it("dibuja solo la primera jugada de cada línea", () => {
    expect(arrowsFromEngineLines([engineLine(1, 0, "g1f3", "d7d5", "d2d4")])[0].uci).toBe(
      "g1f3",
    );
  });

  it("no dibuja más de tres flechas: el tablero deja de leerse", () => {
    const manyLines = [1, 2, 3, 4, 5].map((rank) => engineLine(rank, 0, "e2e4"));
    expect(arrowsFromEngineLines(manyLines)).toHaveLength(3);
  });

  it("aguanta que no haya líneas, o que una venga sin jugadas", () => {
    expect(arrowsFromEngineLines(undefined)).toEqual([]);
    expect(arrowsFromEngineLines([engineLine(1, 0)])).toEqual([]);
  });
});

describe("arrowsFromPreviewLine", () => {
  it("numera la continuación y destaca dónde termina", () => {
    expect(arrowsFromPreviewLine(["g1f3", "d7d5", "d2d4"])).toEqual([
      { uci: "g1f3", brush: "paleBlue", label: "1" },
      { uci: "d7d5", brush: "paleBlue", label: "2" },
      { uci: "d2d4", brush: "blue", label: "3" },
    ]);
  });

  it("una sola jugada ya es el final de su línea", () => {
    expect(arrowsFromPreviewLine(["g1f3"])).toEqual([{ uci: "g1f3", brush: "blue", label: "1" }]);
  });
});

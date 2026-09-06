import { describe, expect, it } from "vitest";
import { buildBoardConfig } from "../boardConfig";

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

    const enUndefined = Object.keys(config).filter((k) => config[k] === undefined);
    expect(enUndefined).toEqual(["lastMove"]);
  });

  it("resalta la última jugada y la limpia cuando no hay", () => {
    expect(buildBoardConfig({ ...BASE, lastMoveUci: "e2e4" }).lastMove).toEqual(["e2", "e4"]);
    expect(buildBoardConfig(BASE).lastMove).toBeUndefined();
  });

  it("dibuja la flecha de la mejor jugada, o ninguna", () => {
    const con = buildBoardConfig({ ...BASE, bestMoveUci: "g1f3" });
    expect(con.drawable?.autoShapes).toEqual([{ orig: "g1", dest: "f3", brush: "green" }]);

    expect(buildBoardConfig(BASE).drawable?.autoShapes).toEqual([]);
  });

  it("recorta bien la promoción en el UCI de cuatro o cinco caracteres", () => {
    expect(buildBoardConfig({ ...BASE, lastMoveUci: "e7e8q" }).lastMove).toEqual(["e7", "e8"]);
  });
});

/** Copia literal del `deepMerge` de chessground (src/config.ts): hace
 * `base[k] = nuevo[k]` sin comprobar si el valor es `undefined`. */
type Mutable = Record<string, unknown>;

function deepMergeComoChessground(base: Mutable, extend: Mutable): void {
  for (const key in extend) {
    if (key === "__proto__" || key === "constructor" || !Object.prototype.hasOwnProperty.call(extend, key))
      continue;
    if (
      Object.prototype.hasOwnProperty.call(base, key) &&
      isPlainObject(base[key]) &&
      isPlainObject(extend[key])
    )
      deepMergeComoChessground(base[key] as Mutable, extend[key] as Mutable);
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
    const estado: Mutable = {
      movable: { free: false, showDests: true, events: {}, rookCastle: true },
      turnColor: "white",
    };

    // Varias actualizaciones seguidas, como al navegar por la partida.
    for (const lastMoveUci of [null, "e2e4", "e7e5", null]) {
      deepMergeComoChessground(estado, buildBoardConfig({ ...BASE, lastMoveUci }) as Mutable);
    }

    // Antes del arreglo, `movable` acababa en undefined y la siguiente
    // llamada fallaba al escribir `state.movable.dests`.
    expect(estado.movable).toBeDefined();
    expect((estado.movable as Mutable).rookCastle).toBe(true);
    expect(estado.turnColor).toBe("white");
  });

  it("el tablero interactivo sí reemplaza los destinos, sin romper el resto", () => {
    const estado: Mutable = {
      movable: { free: false, showDests: true, events: { after: () => {} }, rookCastle: true },
      turnColor: "white",
    };

    deepMergeComoChessground(
      estado,
      buildBoardConfig({
        ...BASE,
        legalMoves: new Map([["e2", ["e4"]]]),
        turnColor: "black",
      }) as Mutable,
    );

    const movable = estado.movable as { dests: Map<string, string[]>; events: Mutable };
    expect(movable.dests.get("e2")).toEqual(["e4"]);
    expect(movable.events.after).toBeTypeOf("function"); // no se pierde
    expect(estado.turnColor).toBe("black");
  });
});

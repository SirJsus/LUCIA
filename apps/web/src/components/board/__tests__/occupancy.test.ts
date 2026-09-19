/** Las reglas de conteo de RF-7 sobre posiciones montadas a mano, cada una con
 * lo mínimo para que se vea qué se está comprobando. */
import { describe, expect, it } from "vitest";
import { computeOccupancy, coverageFrom, sortAttacksByValue } from "../occupancy";

/** Atajo: el mapa de una posición que se sabe válida. */
function occupancyOf(fen: string) {
  const occupancy = computeOccupancy(fen);
  if (!occupancy) throw new Error(`FEN no válido en la prueba: ${fen}`);
  return occupancy;
}

/** Las casillas desde las que ataca directamente un bando. */
function directFrom(fen: string, square: string, color: "w" | "b"): string[] {
  return occupancyOf(fen)
    .squares[square].directAttacks[color].map((attack) => attack.from)
    .sort();
}

describe("computeOccupancy", () => {
  it("devuelve null si el FEN no se puede leer", () => {
    expect(computeOccupancy("")).toBeNull();
    expect(computeOccupancy("esto no es un FEN")).toBeNull();
  });

  it("cuenta las 64 casillas aunque estén vacías", () => {
    const occupancy = occupancyOf("8/8/8/8/8/8/8/K6k w - - 0 1");
    expect(Object.keys(occupancy.squares)).toHaveLength(64);
    expect(occupancy.squares.d4.balance).toBe(0);
  });
});

describe("reglas de conteo (RF-7.7)", () => {
  it("el peón cubre sus dos diagonales y no la casilla de delante", () => {
    const fen = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1";
    expect(directFrom(fen, "d3", "w")).toContain("e2");
    expect(directFrom(fen, "f3", "w")).toContain("e2");
    expect(directFrom(fen, "e3", "w")).not.toContain("e2");
  });

  it("el rey cuenta como atacante", () => {
    expect(directFrom("4k3/8/8/8/8/8/8/4K3 w - - 0 1", "e2", "w")).toEqual(["e1"]);
  });

  it("la casilla de captura al paso la ataca el peón que capturaría ahí", () => {
    // Las negras acaban de jugar d7-d5 y el peón blanco de e5 puede capturar
    // al paso en d6, que está vacía.
    const fen = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3";
    expect(directFrom(fen, "d6", "w")).toContain("e5");
  });
});

describe("rayos X aparte del conteo directo (RF-7.5)", () => {
  it("la torre de atrás de una batería llega por rayo X, no directamente", () => {
    // Torres blancas en a1 y a2; la de a1 alcanza a8 solo a través de la otra.
    const occupancy = occupancyOf("k7/8/8/8/8/8/R7/R3K3 w - - 0 1");
    expect(occupancy.squares.a4.directAttacks.w.map((attack) => attack.from)).toEqual(["a2"]);
    const xrayFromA1 = occupancy.squares.a4.xrayAttacks.w.find((attack) => attack.from === "a1");
    expect(xrayFromA1?.throughSquare).toBe("a2");
    // El balance solo cuenta lo directo: una torre, no dos.
    expect(occupancy.squares.a4.balance).toBe(1);
  });

  it("el rayo X se corta en la segunda pieza de la línea", () => {
    // Torre blanca en a1, peones negros en a2 y a3: el rayo llega hasta a3 y
    // no sigue a a4.
    const occupancy = occupancyOf("k7/8/8/8/8/p7/p7/R3K3 w - - 0 1");
    expect(occupancy.squares.a3.xrayAttacks.w.map((attack) => attack.from)).toEqual(["a1"]);
    expect(occupancy.squares.a4.xrayAttacks.w).toEqual([]);
  });
});

describe("piezas clavadas (RF-7.6)", () => {
  it("marca la pieza clavada y la deja contando como atacante", () => {
    // Caballo blanco en e2 entre su rey en e1 y la torre negra de e8.
    const occupancy = occupancyOf("4rk2/8/8/8/8/8/4N3/4K3 w - - 0 1");
    expect(occupancy.pinnedSquares).toEqual(["e2"]);
    const attackOnD4 = occupancy.squares.d4.directAttacks.w.find((attack) => attack.from === "e2");
    expect(attackOnD4?.isPinned).toBe(true);
  });

  it("no hay clavada si algo se interpone entre el rey y la pieza", () => {
    // El mismo caballo, pero con un peón blanco en e3 que corta la línea.
    expect(occupancyOf("4rk2/8/8/8/4N3/4P3/8/4K3 w - - 0 1").pinnedSquares).toEqual([]);
  });

  it("no hay clavada si la pieza de la línea no se desliza por ella", () => {
    // Una torre negra clava en columna; un alfil negro en la misma columna, no.
    expect(occupancyOf("4bk2/8/8/8/8/8/4N3/4K3 w - - 0 1").pinnedSquares).toEqual([]);
  });
});

describe("piezas colgadas (RF-7.4)", () => {
  it("marca la pieza atacada que nadie defiende", () => {
    // Torre negra en d8 atacando al caballo blanco de d4, sin defensa.
    expect(occupancyOf("3rk3/8/8/8/3N4/8/8/4K3 w - - 0 1").hangingSquares).toEqual(["d4"]);
  });

  it("no marca la pieza atacada que sí está defendida", () => {
    // El mismo caballo, ahora defendido por un peón blanco en c3.
    expect(occupancyOf("3rk3/8/8/8/3N4/2P5/8/4K3 w - - 0 1").hangingSquares).toEqual([]);
  });

  it("marca la pieza defendida si la ataca una de menor valor", () => {
    // Dama blanca en d4 atacada por el peón negro de e5 y defendida por su rey
    // en c3: la defensa no la salva, porque el cambio ya es malo. El peón de
    // e5, atacado por la dama pero defendido por el de f6, no está colgado.
    expect(occupancyOf("4k3/8/5p2/4p3/3Q4/2K5/8/8 w - - 0 1").hangingSquares).toEqual(["d4"]);
  });

  it("no cuenta al rey entre las piezas colgadas", () => {
    // Rey blanco en jaque de la torre negra: eso es jaque, no material colgado.
    expect(occupancyOf("4rk2/8/8/8/8/8/8/4K3 b - - 0 1").hangingSquares).toEqual([]);
  });
});

describe("balance del mapa de calor (RF-7.1)", () => {
  it("resta atacantes negros de blancos sin contar los rayos X", () => {
    // e4 la cubren el peón blanco de d3 y los negros de d5 y f5.
    const occupancy = occupancyOf("4k3/8/8/3p1p2/8/3P4/8/4K3 w - - 0 1");
    expect(occupancy.squares.e4.balance).toBe(-1);
  });
});

describe("coverageFrom", () => {
  it("separa lo que una pieza cubre de lo que alcanza por rayo X", () => {
    const occupancy = occupancyOf("k7/8/8/8/8/8/R7/R3K3 w - - 0 1");
    const coverage = coverageFrom(occupancy, "a1");
    expect(coverage.directSquares).toContain("a2");
    expect(coverage.xraySquares).toContain("a8");
    expect(coverage.directSquares).not.toContain("a8");
  });
});

describe("sortAttacksByValue", () => {
  it("ordena de la pieza más valiosa a la menos, para la inspección", () => {
    // d4 la cubren una dama en d1, una torre en d8 y un peón en e3.
    const occupancy = occupancyOf("3rk3/8/8/8/8/4P3/8/3QK3 w - - 0 1");
    const d4 = occupancy.squares.d4.directAttacks;
    const all = sortAttacksByValue([...d4.w, ...d4.b]);
    expect(all.map((attack) => attack.from)).toEqual(["d1", "d8", "e3"]);
  });
});

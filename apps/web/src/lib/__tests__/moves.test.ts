import { describe, expect, it } from "vitest";
import { formatMoveSequence, moveNumberLabel, moveNumberOf, plyFromFen, turnsOf } from "../moves";

const STANDARD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

describe("plyFromFen", () => {
  it("da 0 en la posición estándar, para que sumarlo no cambie nada", () => {
    expect(plyFromFen(STANDARD)).toBe(0);
  });

  it("cuenta las medias jugadas ya jugadas en una posición cualquiera", () => {
    // Turno 12, mueven las negras: 11 jugadas enteras + la de las blancas.
    expect(plyFromFen("8/8/8/8/8/8/8/K6k b - - 0 12")).toBe(23);
    expect(plyFromFen("8/8/8/8/8/8/8/K6k w - - 0 12")).toBe(22);
  });

  it("no se rompe con un FEN incompleto", () => {
    expect(plyFromFen("")).toBe(0);
  });
});

describe("moveNumberOf / moveNumberLabel", () => {
  it("empareja cada turno con sus dos plies", () => {
    expect(moveNumberOf(0)).toBe(1);
    expect(moveNumberOf(1)).toBe(1);
    expect(moveNumberOf(2)).toBe(2);
  });

  it("distingue la jugada de las negras con los tres puntos del PGN", () => {
    expect(moveNumberLabel(0)).toBe("1.");
    expect(moveNumberLabel(1)).toBe("1...");
    expect(moveNumberLabel(22)).toBe("12.");
  });
});

describe("formatMoveSequence", () => {
  it("numera cada turno y deja la jugada de negras pegada a la de blancas", () => {
    expect(formatMoveSequence(["e4", "e5", "Cf3", "Cc6"])).toBe("1. e4 e5 2. Cf3 Cc6");
  });

  it("no numera una lista vacía", () => {
    expect(formatMoveSequence([])).toBe("");
  });

  it("cierra el turno impar sin repetir el número", () => {
    expect(formatMoveSequence(["e4", "e5", "Cf3"])).toBe("1. e4 e5 2. Cf3");
  });
});

describe("turnsOf", () => {
  /** Las jugadas de una partida de sparring: su ply es el sitio que ocupan en
   * la lista, más el de la posición desde la que se empezó a jugar. */
  const sparringPly = (startingPly: number) => (_san: string, index: number) =>
    startingPly + index;

  it("empareja las jugadas por turno y deja el hueco de la última suelta", () => {
    expect(turnsOf(["e4", "e5", "Cf3"], sparringPly(0))).toEqual([
      { number: 1, white: "e4", black: "e5" },
      { number: 2, white: "Cf3", black: null },
    ]);
  });

  it("numera desde la jugada real cuando la partida se retomó a mitad", () => {
    // Ply 44: turno 23, mueven las blancas (fila 101 del inventario).
    expect(turnsOf(["Txd4", "exd4"], sparringPly(44))).toEqual([
      { number: 23, white: "Txd4", black: "exd4" },
    ]);
  });

  it("deja el primer turno sin jugada de blancas si se retomó con negras", () => {
    // Ply 45: turno 23, mueven las negras, así que ese turno ya está a medias.
    expect(turnsOf(["Dxd4", "exd4"], sparringPly(45))).toEqual([
      { number: 23, white: null, black: "Dxd4" },
      { number: 24, white: "exd4", black: null },
    ]);
  });

  it("sitúa cada jugada por su ply, que es lo que trae la lista analizada", () => {
    const moves = [{ ply: 0 }, { ply: 1 }, { ply: 2 }];
    expect(turnsOf(moves, (move) => move.ply)).toEqual([
      { number: 1, white: { ply: 0 }, black: { ply: 1 } },
      { number: 2, white: { ply: 2 }, black: null },
    ]);
  });
});

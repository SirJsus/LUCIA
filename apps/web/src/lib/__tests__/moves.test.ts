import { describe, expect, it } from "vitest";
import { moveNumberLabel, moveNumberOf, plyFromFen } from "../moves";

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

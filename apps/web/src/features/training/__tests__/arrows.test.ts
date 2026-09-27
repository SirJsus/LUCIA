import { describe, expect, it } from "vitest";
import { arrowsFromPuzzleAnswer } from "../arrows";

const STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

describe("arrowsFromPuzzleAnswer", () => {
  it("destaca la mejor jugada y atenúa las equivalentes", () => {
    const arrows = arrowsFromPuzzleAnswer(STARTING_FEN, ["e4", "d4"], null);

    expect(arrows).toEqual([
      { uci: "e2e4", brush: "green", label: "e4" },
      { uci: "d2d4", brush: "paleGreen", label: "d4" },
    ]);
  });

  it("pinta en rojo la jugada que se hizo en la partida", () => {
    const arrows = arrowsFromPuzzleAnswer(STARTING_FEN, ["e4"], "a3");

    expect(arrows.at(-1)).toEqual({ uci: "a2a3", brush: "red", label: "a3" });
  });

  it("no dibuja una jugada que no encaja en la posición", () => {
    expect(arrowsFromPuzzleAnswer(STARTING_FEN, ["Qxh7"], "e9")).toEqual([]);
  });

  it("sin solución no dibuja nada", () => {
    expect(arrowsFromPuzzleAnswer(STARTING_FEN, [], null)).toEqual([]);
  });
});

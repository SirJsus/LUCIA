/** Cómo se lee un drill de aperturas en pantalla (RF-4.2).
 *
 * Lo que se fija aquí es el motivo —que la frase diga lo que la baraja
 * dice— y el conteo de jugadas propias, que es lo que no se puede sacar del
 * `length_plies` sin mirar de qué color se juega.
 */
import type { Drill } from "@lucia/shared-types";
import { describe, expect, it } from "vitest";
import { playerMoveCount, reasonLabel, reasonSentence } from "../drills";

function drill(overrides: Partial<Drill>): Drill {
  return {
    id: 1,
    reason: "departure",
    player_color: "white",
    opening_eco: "B00",
    opening_name: "Owen Defense",
    games: 3,
    score_percent: 0,
    fen: "",
    first_player_ply: 0,
    preceding_moves_san: [],
    length_plies: 2,
    due_at: "2026-09-21T10:00:00Z",
    repetitions: 0,
    ...overrides,
  };
}

describe("reasonSentence", () => {
  it("cuenta lo que dice cada baraja", () => {
    expect(reasonSentence(drill({ reason: "departure", games: 4, score_percent: 25 }))).toBe(
      "Abandonas la teoría aquí en 4 partidas y sacas un 25.0 %.",
    );
    expect(reasonSentence(drill({ reason: "opening", games: 10, score_percent: 30 }))).toBe(
      "Con esta apertura sacas un 30.0 % en 10 partidas.",
    );
  });

  it("concuerda el singular", () => {
    expect(reasonSentence(drill({ games: 1 }))).toContain("1 partida y");
  });
});

describe("reasonLabel", () => {
  it("nombra las dos barajas y deja pasar lo que no conoce", () => {
    expect(reasonLabel("departure")).toBe("Te sales de la teoría");
    expect(reasonLabel("opening")).toBe("Apertura floja");
    expect(reasonLabel("vete a saber")).toBe("vete a saber");
  });
});

describe("el conteo de jugadas propias", () => {
  it("con blancas empieza en la primera del todo", () => {
    // e4 c5 Cf3 -> dos jugadas de blancas.
    const line = drill({ player_color: "white", first_player_ply: 0, length_plies: 3 });
    expect(playerMoveCount(line)).toBe(2);
  });

  it("con negras la primera del rival no cuenta", () => {
    // e4 c5 Cf3 d6 -> dos jugadas de negras, y la línea abre el rival.
    const line = drill({ player_color: "black", first_player_ply: 1, length_plies: 4 });
    expect(playerMoveCount(line)).toBe(2);
  });
});

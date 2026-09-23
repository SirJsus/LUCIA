/** Cómo se lee una partida de sparring en pantalla (RF-4.3).
 *
 * Lo que se fija aquí es que el marcador se traduzca desde quien juega: "0-1"
 * es una victoria o una derrota según el color que se llevara, y confundirlos
 * sería decirle a alguien que ganó una partida que perdió.
 */
import type { SparringGame } from "@lucia/shared-types";
import { describe, expect, it } from "vitest";
import { outcomeFor, outcomeSentence, turnsOf } from "../sparring";

function game(overrides: Partial<SparringGame>): SparringGame {
  return {
    id: 1,
    player_color: "white",
    engine: "stockfish",
    engine_elo: 1500,
    origin_game_id: null,
    origin_ply: null,
    starting_ply: 0,
    fen: "",
    moves_san: [],
    last_move_uci: null,
    is_player_turn: true,
    result: null,
    termination: null,
    pgn: "",
    created_at: "2026-09-21T10:00:00Z",
    updated_at: "2026-09-21T10:00:00Z",
    ...overrides,
  };
}

describe("outcomeFor", () => {
  it("deja sin resultado la partida que sigue viva", () => {
    expect(outcomeFor(game({ result: null }))).toBeNull();
  });

  it("lee el mismo marcador al revés según el color de quien juega", () => {
    expect(outcomeFor(game({ player_color: "white", result: "1-0" }))).toBe("win");
    expect(outcomeFor(game({ player_color: "black", result: "1-0" }))).toBe("loss");
    expect(outcomeFor(game({ player_color: "black", result: "0-1" }))).toBe("win");
  });

  it("las tablas son tablas para los dos", () => {
    expect(outcomeFor(game({ player_color: "white", result: "1/2-1/2" }))).toBe("draw");
    expect(outcomeFor(game({ player_color: "black", result: "1/2-1/2" }))).toBe("draw");
  });
});

describe("outcomeSentence", () => {
  it("dice también por qué acabó, que es lo que el marcador no distingue", () => {
    expect(outcomeSentence(game({ result: "1-0", termination: "checkmate" }))).toBe(
      "Ganaste por jaque mate",
    );
    expect(outcomeSentence(game({ result: "0-1", termination: "resignation" }))).toBe(
      "Perdiste por abandono",
    );
  });

  it("se queda en el resultado si la causa no se reconoce", () => {
    expect(outcomeSentence(game({ result: "1-0", termination: "vete a saber" }))).toBe("Ganaste");
  });
});

describe("turnsOf", () => {
  it("empareja las jugadas por turno y deja el hueco de la última suelta", () => {
    expect(turnsOf(["e4", "e5", "Cf3"])).toEqual([
      { number: 1, white: "e4", black: "e5" },
      { number: 2, white: "Cf3", black: null },
    ]);
  });

  it("numera desde la jugada real cuando la partida se retomó a mitad", () => {
    // Ply 44: turno 23, mueven las blancas (fila 101 del inventario).
    expect(turnsOf(["Txd4", "exd4"], 44)).toEqual([{ number: 23, white: "Txd4", black: "exd4" }]);
  });

  it("deja el primer turno sin jugada de blancas si se retomó con negras", () => {
    // Ply 45: turno 23, mueven las negras, así que ese turno ya está a medias.
    expect(turnsOf(["Dxd4", "exd4"], 45)).toEqual([
      { number: 23, white: null, black: "Dxd4" },
      { number: 24, white: "exd4", black: null },
    ]);
  });
});

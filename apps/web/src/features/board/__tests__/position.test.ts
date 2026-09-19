/** Los criterios del editor de posición (RF-6.1), escritos como tests.
 *
 * Componer un FEN a mano se equivoca en silencio: la cadena sigue pareciendo
 * un FEN y describe otra posición. De ahí que el ida y vuelta y el conteo de
 * casillas vacías tengan caso propio.
 */
import { Chess } from "chess.js";
import { describe, expect, it } from "vitest";
import {
  EMPTY_POSITION,
  enPassantSquares,
  fromFen,
  positionError,
  toFen,
  type EditablePosition,
} from "../position";

const START_FEN = new Chess().fen();

describe("toFen", () => {
  it("cuenta las casillas vacías seguidas, no una por una", () => {
    const position: EditablePosition = {
      ...EMPTY_POSITION,
      pieces: { e1: "K", e8: "k" },
    };
    expect(toFen(position)).toBe("4k3/8/8/8/8/8/8/4K3 w - - 0 1");
  });

  it("recorre los rangos del 8 al 1, como el estándar", () => {
    // Una torre blanca en a1 va al final de la cadena, no al principio.
    const position: EditablePosition = {
      ...EMPTY_POSITION,
      pieces: { a1: "R", a8: "r", e1: "K", e8: "k" },
    };
    expect(toFen(position)).toBe("r3k3/8/8/8/8/8/8/R3K3 w - - 0 1");
  });

  it("escribe un guion donde no hay enroque ni captura al paso", () => {
    expect(toFen({ ...EMPTY_POSITION, pieces: { e1: "K", e8: "k" } })).toContain(" w - - ");
  });

  it("lleva el turno, los enroques y la casilla al paso", () => {
    const position: EditablePosition = {
      pieces: { e1: "K", e8: "k" },
      turn: "b",
      castling: "Kq",
      enPassant: "e3",
    };
    expect(toFen(position)).toBe("4k3/8/8/8/8/8/8/4K3 b Kq e3 0 1");
  });

  it("deja el reloj en 0 1: una posición montada no viene de ninguna partida", () => {
    expect(toFen({ ...EMPTY_POSITION, pieces: { e1: "K", e8: "k" } })).toMatch(/ 0 1$/);
  });
});

describe("fromFen", () => {
  it("sobrevive a la ida y vuelta desde la posición inicial", () => {
    const parsed = fromFen(START_FEN)!;
    expect(toFen(parsed)).toBe(START_FEN);
  });

  it("lee el turno, los enroques y la casilla al paso", () => {
    const parsed = fromFen("4k3/8/8/8/8/8/8/4K3 b Kq e3 0 1")!;
    expect(parsed.turn).toBe("b");
    expect(parsed.castling).toBe("Kq");
    expect(parsed.enPassant).toBe("e3");
    expect(parsed.pieces).toEqual({ e1: "K", e8: "k" });
  });

  it("deja vacíos los campos que el FEN marca con guion", () => {
    const parsed = fromFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")!;
    expect(parsed.castling).toBe("");
    expect(parsed.enPassant).toBeNull();
  });

  it("rechaza lo que no describe un tablero de ocho por ocho", () => {
    expect(fromFen("esto no es un fen")).toBeNull();
    expect(fromFen("4k3/8/8/8/8/8/4K3 w - - 0 1")).toBeNull(); // siete rangos
    expect(fromFen("4k4/8/8/8/8/8/8/4K3 w - - 0 1")).toBeNull(); // nueve columnas
  });
});

describe("positionError", () => {
  it("acepta una posición que podría darse en una partida", () => {
    expect(positionError(START_FEN)).toBeNull();
    expect(positionError("4k3/8/8/8/8/8/8/4K3 w - - 0 1")).toBeNull();
  });

  it("explica en castellano qué falta, no en el inglés de chess.js", () => {
    expect(positionError("8/8/8/8/8/8/8/4K3 w - - 0 1")).toMatch(/rey negro/);
    expect(positionError("4k3/8/8/8/8/8/8/8 w - - 0 1")).toMatch(/rey blanco/);
    expect(positionError("4k3/8/8/8/8/8/8/3KK3 w - - 0 1")).toMatch(/más de un rey blanco/);
    expect(positionError("P3k3/8/8/8/8/8/8/4K3 w - - 0 1")).toMatch(/peones en la primera/);
  });

  it("rechaza que el bando que no mueve esté dando jaque", () => {
    // Las blancas mueven y el rey negro está en jaque de la torre: en una
    // partida real eso no se da, y el motor lo rechazaría. chess.js no lo
    // comprueba, así que lo comprueba el editor.
    expect(positionError("R3k3/8/8/8/8/8/8/4K3 w - - 0 1")).toMatch(/no mueve está en jaque/);
    // Con el turno al revés es una posición normal: jaque a quien le toca.
    expect(positionError("R3k3/8/8/8/8/8/8/4K3 b - - 0 1")).toBeNull();
  });
});

describe("enPassantSquares", () => {
  it("ofrece la fila que corresponde a quien acaba de mover", () => {
    // Si mueven las blancas, el peón que acaba de avanzar dos es negro y la
    // marca está en la sexta fila.
    expect(enPassantSquares("w")).toEqual(["a6", "b6", "c6", "d6", "e6", "f6", "g6", "h6"]);
    expect(enPassantSquares("b")).toEqual(["a3", "b3", "c3", "d3", "e3", "f3", "g3", "h3"]);
  });
});

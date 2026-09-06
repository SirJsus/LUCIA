import { describe, expect, it } from "vitest";
import { formatAccuracy, formatTimeControl, gameResult } from "../format";

describe("gameResult", () => {
  it("traduce la victoria de las blancas", () => {
    expect(gameResult({ white_result: "win" })).toBe("1-0");
  });

  it("cualquier resultado no ganador ni de tablas es derrota de las blancas", () => {
    expect(gameResult({ white_result: "checkmated" })).toBe("0-1");
    expect(gameResult({ white_result: "resigned" })).toBe("0-1");
    expect(gameResult({ white_result: "timeout" })).toBe("0-1");
  });

  it("reconoce las formas de tablas que reporta chess.com", () => {
    expect(gameResult({ white_result: "agreed" })).toBe("½-½");
    expect(gameResult({ white_result: "stalemate" })).toBe("½-½");
    expect(gameResult({ white_result: "repetition" })).toBe("½-½");
    expect(gameResult({ white_result: "insufficient" })).toBe("½-½");
  });
});

describe("formatTimeControl", () => {
  it("convierte segundos a minutos", () => {
    expect(formatTimeControl("180")).toBe("3+0");
    expect(formatTimeControl("600")).toBe("10+0");
  });

  it("conserva el incremento", () => {
    expect(formatTimeControl("600+5")).toBe("10+5");
  });

  it("no rompe con controles que no son numéricos (correspondencia)", () => {
    expect(formatTimeControl("1/86400")).toBe("1/86400");
  });
});

describe("formatAccuracy", () => {
  it("muestra un guion cuando todavía no hay análisis", () => {
    expect(formatAccuracy(null)).toBe("—");
    expect(formatAccuracy(undefined)).toBe("—");
  });

  it("redondea a un decimal", () => {
    expect(formatAccuracy(93.4567)).toBe("93.5");
  });
});

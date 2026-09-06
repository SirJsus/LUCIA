import { describe, expect, it } from "vitest";
import { formatScore } from "../score";

describe("formatScore", () => {
  it("muestra centipawns como peones con signo", () => {
    expect(formatScore({ score_cp: 35, score_mate: null })).toBe("+0.35");
    expect(formatScore({ score_cp: -250, score_mate: null })).toBe("−2.50");
    expect(formatScore({ score_cp: 0, score_mate: null })).toBe("+0.00");
  });

  it("muestra el mate con su distancia y a favor de quién", () => {
    expect(formatScore({ score_cp: null, score_mate: 3 })).toBe("M3+");
    expect(formatScore({ score_cp: null, score_mate: -2 })).toBe("M2−");
  });

  it("el mate manda sobre los centipawns si vinieran ambos", () => {
    expect(formatScore({ score_cp: 900, score_mate: 1 })).toBe("M1+");
  });

  it("no revienta si no hay evaluación", () => {
    expect(formatScore({ score_cp: null, score_mate: null })).toBe("—");
  });
});

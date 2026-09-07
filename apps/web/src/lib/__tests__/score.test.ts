import { describe, expect, it } from "vitest";
import { formatScore, whiteWinPercentAfterMove, whiteWinPercentFromScore } from "../score";

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

describe("whiteWinPercentFromScore", () => {
  it("una posición igualada es 50-50", () => {
    expect(whiteWinPercentFromScore({ score_cp: 0, score_mate: null })).toBe(50);
  });

  it("sigue el modelo de Lichess, el mismo que usa el backend", () => {
    // 1000 / (1 + exp(-0.00368208 * cp)), redondeado, entre diez.
    expect(whiteWinPercentFromScore({ score_cp: 100, score_mate: null })).toBeCloseTo(59.1, 1);
    expect(whiteWinPercentFromScore({ score_cp: -100, score_mate: null })).toBeCloseTo(40.9, 1);
  });

  it("acota las ventajas enormes: de +10 a +30 la partida está igual de ganada", () => {
    const atPlusTen = whiteWinPercentFromScore({ score_cp: 1000, score_mate: null });
    expect(whiteWinPercentFromScore({ score_cp: 3000, score_mate: null })).toBe(atPlusTen);
    expect(atPlusTen).toBeLessThan(100);
  });

  it("un mate no se modela: se gana o se pierde", () => {
    expect(whiteWinPercentFromScore({ score_cp: null, score_mate: 3 })).toBe(100);
    expect(whiteWinPercentFromScore({ score_cp: null, score_mate: -1 })).toBe(0);
    // M0 = a quien le toca mover ya está mateado.
    expect(whiteWinPercentFromScore({ score_cp: null, score_mate: 0 })).toBe(0);
  });

  it("sin evaluación no inventa un empate", () => {
    expect(whiteWinPercentFromScore({ score_cp: null, score_mate: null })).toBeNull();
  });
});

describe("whiteWinPercentAfterMove", () => {
  it("deja igual lo que ya viene desde las blancas", () => {
    expect(whiteWinPercentAfterMove({ color: "white", win_percent_after: 62 })).toBe(62);
  });

  it("da la vuelta a lo que viene desde las negras", () => {
    expect(whiteWinPercentAfterMove({ color: "black", win_percent_after: 62 })).toBe(38);
  });
});

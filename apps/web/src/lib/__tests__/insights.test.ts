import { describe, expect, it } from "vitest";
import {
  criticalMomentStyle,
  formatTimeLeftBucket,
  mistakeTypeStyle,
  formatTrendSentence,
} from "../insights";

describe("etiquetas de los patrones", () => {
  it("traduce cada tipo de error con su explicación", () => {
    expect(mistakeTypeStyle("time").label).toBe("Con el reloj encima");
    expect(mistakeTypeStyle("tactical").description).toContain("captura");
  });

  it("traduce cada motivo de momento crítico", () => {
    expect(criticalMomentStyle("only_move").label).toBe("Solo valía una jugada");
    expect(criticalMomentStyle("swing").tone).toBe("danger");
  });

  it("no se rompe con un valor que la API todavía no enseñaba", () => {
    expect(mistakeTypeStyle("lo-que-sea").label).toBe("Sin clasificar");
    expect(criticalMomentStyle("lo-que-sea").label).toBe("Sin clasificar");
  });
});

describe("formatTimeLeftBucket", () => {
  it("dice el tramo en la unidad que se lee de un vistazo", () => {
    expect(formatTimeLeftBucket(null)).toBe("más de 1 min");
    expect(formatTimeLeftBucket(60)).toBe("menos de 1 min");
    expect(formatTimeLeftBucket(10)).toBe("menos de 10 s");
  });
});

describe("formatTrendSentence", () => {
  it("dice con palabras si mejoras, que el signo solo no lo dice", () => {
    // En precisión subir es mejorar; en errores, empeorar.
    expect(
      formatTrendSentence({ baseline_months: 3, accuracy_change: 1.8, mistake_rate_change: -0.4 }),
    ).toBe(
      "Respecto a los 3 meses anteriores, tu precisión sube 1.8 puntos y los errores bajan 0.4 por cada cien jugadas.",
    );
  });

  it("concuerda la frase cuando solo hay un mes de referencia", () => {
    expect(
      formatTrendSentence({ baseline_months: 1, accuracy_change: -2.0, mistake_rate_change: 1.5 }),
    ).toBe(
      "Respecto al mes anterior, tu precisión baja 2.0 puntos y los errores suben 1.5 por cada cien jugadas.",
    );
  });

  it("no llama cambio a un cambio que se redondea a cero", () => {
    expect(
      formatTrendSentence({ baseline_months: 2, accuracy_change: 0.01, mistake_rate_change: -0.02 }),
    ).toBe("Respecto a los 2 meses anteriores, tu precisión se mantiene y los errores siguen igual.");
  });
});

import { describe, expect, it } from "vitest";
import { criticalMomentStyle, formatTimeLeftBucket, mistakeTypeStyle } from "../insights";

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

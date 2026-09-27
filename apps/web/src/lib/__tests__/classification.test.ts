import { describe, expect, it } from "vitest";
import { classificationStyle } from "../classification";

describe("classificationStyle", () => {
  it("da etiqueta en español y símbolo para cada categoría conocida", () => {
    expect(classificationStyle("blunder").label).toBe("Blunder");
    expect(classificationStyle("best").symbol).toBe("★");
    expect(classificationStyle("missed_win").label).toBe("Perdió el mate");
  });

  it("no revienta ante una categoría que la API todavía no conoce", () => {
    // El backend podría añadir categorías nuevas antes que el front.
    const style = classificationStyle("categoria_futura");
    expect(style.label).toBe("Sin clasificar");
    expect(style.color).toBeTruthy();
  });
});

import { describe, expect, it } from "vitest";
import {
  formatAccuracy,
  formatDuration,
  formatEngineName,
  formatPercent,
  formatPerHundredMoves,
  formatRating,
  formatTimeClass,
  formatTimeControl,
  formatYearMonth,
  gameResult,
} from "../format";

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

  it("reconoce las tablas del PGN importado a mano, que no dicen cómo acabó", () => {
    expect(gameResult({ white_result: "draw" })).toBe("½-½");
  });
});

describe("formatRating", () => {
  it("enseña el rating cuando se sabe", () => {
    expect(formatRating(1832)).toBe("1832");
  });

  it("enseña un hueco cuando el PGN no traía rating, en vez de un 0", () => {
    expect(formatRating(0)).toBe("—");
  });

  it("enseña el mismo hueco cuando no hay rating de ese mes o de ese control", () => {
    expect(formatRating(null)).toBe("—");
    expect(formatRating(undefined)).toBe("—");
  });
});

describe("formatPerHundredMoves", () => {
  it("da un decimal, que es lo que distingue dos meses", () => {
    expect(formatPerHundredMoves(1.44)).toBe("1.4");
    expect(formatPerHundredMoves(0)).toBe("0.0");
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

  it("enseña un hueco cuando el PGN importado no decía el control", () => {
    expect(formatTimeControl("-")).toBe("—");
  });
});

describe("formatAccuracy", () => {
  it("muestra un guion cuando todavía no hay análisis", () => {
    expect(formatAccuracy(null)).toBe("—");
    expect(formatAccuracy(undefined)).toBe("—");
  });

  it("redondea a un decimal y lleva la unidad, que es un porcentaje", () => {
    expect(formatAccuracy(93.4567)).toBe("93.5 %");
  });
});

describe("formatDuration", () => {
  it("muestra minutos y segundos con los segundos a dos cifras", () => {
    expect(formatDuration(0)).toBe("0:00");
    expect(formatDuration(9)).toBe("0:09");
    expect(formatDuration(75)).toBe("1:15");
  });

  it("añade las horas solo cuando las hay", () => {
    expect(formatDuration(3599)).toBe("59:59");
    expect(formatDuration(3600)).toBe("1:00:00");
    expect(formatDuration(3725)).toBe("1:02:05");
  });

  it("no rompe con entradas fraccionarias ni negativas", () => {
    expect(formatDuration(12.7)).toBe("0:12");
    expect(formatDuration(-5)).toBe("0:00");
  });
});

describe("formatPercent", () => {
  it("pone la unidad, con el espacio que pide la ortografía española", () => {
    expect(formatPercent(54.28)).toBe("54 %");
    expect(formatPercent(54.28, 1)).toBe("54.3 %");
  });
});

describe("formatEngineName", () => {
  it("enseña los motores conocidos como se escriben de verdad", () => {
    expect(formatEngineName("stockfish")).toBe("Stockfish");
    expect(formatEngineName("lc0")).toBe("Lc0");
  });

  it("un motor que no conoce se capitaliza, no se rompe (RNF-9)", () => {
    expect(formatEngineName("komodo")).toBe("Komodo");
  });
});

describe("formatTimeClass", () => {
  it("presenta los controles de chess.com igual en todas las pantallas", () => {
    // En inglés a propósito: son los términos del dominio y los que el
    // usuario ya ve en chess.com. Ver el comentario de la función.
    expect(formatTimeClass("bullet")).toBe("Bullet");
    expect(formatTimeClass("blitz")).toBe("Blitz");
    expect(formatTimeClass("rapid")).toBe("Rapid");
    expect(formatTimeClass("daily")).toBe("Daily");
  });

  it("uno desconocido se capitaliza en vez de desaparecer", () => {
    expect(formatTimeClass("classical")).toBe("Classical");
  });

  it("el ritmo que el PGN importado no trae es un hueco, no un «Unknown»", () => {
    expect(formatTimeClass("unknown")).toBe("—");
  });
});

describe("formatYearMonth", () => {
  it("rellena el mes a dos cifras para que los meses se ordenen a la vista", () => {
    expect(formatYearMonth(2026, 9)).toBe("2026-09");
    expect(formatYearMonth(2026, 12)).toBe("2026-12");
  });
});

/** Cómo se lee el plan semanal en pantalla (RF-4.5).
 *
 * Lo que se fija aquí es que cada debilidad se cuente **en su unidad**: las
 * cinco clases llegan con el mismo campo `magnitude` y significan cosas
 * distintas, así que confundirlas sería decirle a alguien que pierde 50 puntos
 * de probabilidad cuando lo que pasa es que el 50 % de sus errores son de un
 * tipo.
 */
import type { PlanTask, Weakness } from "@lucia/shared-types";
import { describe, expect, it } from "vitest";
import { formatWeaknessSentence, taskDisplay, taskProgressPercent } from "../plan";

function weakness(overrides: Partial<Weakness>): Weakness {
  return { kind: "phase", subject: "middlegame", magnitude: 10, color: "", ...overrides };
}

describe("formatWeaknessSentence", () => {
  it("cuenta la fase en puntos de probabilidad de victoria", () => {
    expect(formatWeaknessSentence(weakness({ kind: "phase", subject: "endgame", magnitude: 8 }))).toBe(
      "Pierdes 8 pts de prob. de victoria por jugada en final.",
    );
  });

  it("cuenta el tipo de error como parte del total", () => {
    expect(
      formatWeaknessSentence(weakness({ kind: "mistake_type", subject: "tactical", magnitude: 55 })),
    ).toBe("El 55 % de tus errores están clasificados como «Táctico».");
  });

  it("nombra la apertura con el bando, que es lo que la distingue", () => {
    expect(
      formatWeaknessSentence(
        weakness({ kind: "opening", subject: "Caro-Kann Defense", magnitude: 2.5, color: "black" }),
      ),
    ).toBe("Con Caro-Kann Defense de negras pierdes 2.5 puntos.");
  });

  it("cuenta los apuros de reloj como parte de las partidas", () => {
    expect(formatWeaknessSentence(weakness({ kind: "time_trouble", subject: "", magnitude: 40 }))).toBe(
      "Juegas con el reloj encima en el 40 % de tus partidas.",
    );
  });

  it("cuenta la tendencia como puntos de precisión perdidos", () => {
    expect(formatWeaknessSentence(weakness({ kind: "accuracy_trend", subject: "", magnitude: 3.2 }))).toBe(
      "Tu precisión ha bajado 3.2 puntos respecto a los meses anteriores.",
    );
  });
});

describe("las etiquetas y el destino de cada deber", () => {
  it("llevan a la pantalla donde se entrena", () => {
    expect(taskDisplay("puzzles").to).toBe("/training/puzzles");
    expect(taskDisplay("drills").to).toBe("/training/drills");
    expect(taskDisplay("replays").to).toBe("/training/replays");
    expect(taskDisplay("sparring").to).toBe("/training/sparring");
  });

  it("dejan pasar lo que no conocen en vez de romperse", () => {
    expect(taskDisplay("vete a saber").label).toBe("vete a saber");
    expect(taskDisplay("vete a saber").to).toBe("/training");
  });
});

describe("taskProgressPercent", () => {
  it("es la parte hecha del objetivo", () => {
    const task = (done_this_week: number, weekly_target: number) =>
      ({ kind: "puzzles", done_this_week, weekly_target, reasons: [] }) as PlanTask;
    expect(taskProgressPercent(task(0, 10))).toBe(0);
    expect(taskProgressPercent(task(5, 10))).toBe(50);
    expect(taskProgressPercent(task(10, 10))).toBe(100);
  });

  it("no pasa del 100 % aunque se entrene de más", () => {
    expect(
      taskProgressPercent({
        kind: "puzzles",
        done_this_week: 30,
        weekly_target: 10,
        reasons: [],
      } as PlanTask),
    ).toBe(100);
  });

  it("no divide por cero si el objetivo llegara vacío", () => {
    expect(
      taskProgressPercent({
        kind: "puzzles",
        done_this_week: 0,
        weekly_target: 0,
        reasons: [],
      } as PlanTask),
    ).toBe(100);
  });
});

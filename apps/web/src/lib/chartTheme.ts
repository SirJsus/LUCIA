/** Colores de los gráficos, que recharts necesita como valores concretos.
 *
 * Tailwind no llega aquí: recharts pinta el tooltip y las marcas de eje con
 * estilos en línea, así que la paleta oscura hay que dársela a mano. Sin esto
 * el tooltip conservaba su fondo blanco de fábrica sobre el tema oscuro y las
 * marcas de eje su gris `#666`, ilegibles en los dos temas (criterio C-2 de
 * docs/07-coherencia-ui.md, paridad claro/oscuro).
 *
 * El tema vive donde lo dejó `ThemeToggle`: la clase `dark` en `<html>`. Se
 * observa esa clase en vez de leer `localStorage` para no duplicar la regla
 * de qué tema está activo, y para reaccionar al cambio sin recargar.
 */
import { useEffect, useState } from "react";
import type { BadgeTone } from "../components/Badge";

export interface ChartTheme {
  /** Estilo del recuadro del tooltip. */
  tooltipStyle: React.CSSProperties;
  /** Color de las marcas y etiquetas de los ejes. */
  axisColor: string;
  /** Estilo de las etiquetas de los ejes, el mismo tamaño en todos los
   * gráficos: cada uno con el suyo daba ejes de distinto cuerpo en la misma
   * pantalla (criterio C-2 de docs/07-coherencia-ui.md). */
  axisTickStyle: { fontSize: number; fill: string };
  /** Color de la serie principal (curva de evaluación, barras). */
  seriesColor: string;
  /** Color de lo que hay que destacar sobre la serie. */
  highlightColor: string;
  /** Color de la serie de rating, que convive con la de precisión en el
   * mismo gráfico de tendencias y tiene que distinguirse de ella. */
  ratingColor: string;
  /** Un color por tono de `Badge`, para las series que ya tienen una insignia
   * en otra parte de la pantalla: así el mismo tipo de error se reconoce por
   * el color en la tabla de "Por qué fallas" y en el gráfico de tendencias
   * (criterio C-5 de docs/07-coherencia-ui.md). Son las tonalidades 500 y 400
   * de Tailwind, las mismas familias que `TONE_CLASSES`. */
  toneColors: Record<BadgeTone, string>;
}

const LIGHT_THEME: ChartTheme = {
  tooltipStyle: {
    fontSize: 12,
    backgroundColor: "#ffffff",
    border: "1px solid #cbd5e1",
    borderRadius: 4,
    color: "#0f172a",
  },
  axisColor: "#475569",
  axisTickStyle: { fontSize: 11, fill: "#475569" },
  seriesColor: "#6366f1",
  highlightColor: "#ef4444",
  ratingColor: "#10b981",
  toneColors: {
    neutral: "#64748b",
    info: "#0ea5e9",
    success: "#10b981",
    warning: "#f59e0b",
    danger: "#ef4444",
  },
};

const DARK_THEME: ChartTheme = {
  tooltipStyle: {
    fontSize: 12,
    backgroundColor: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 4,
    color: "#e2e8f0",
  },
  axisColor: "#94a3b8",
  axisTickStyle: { fontSize: 11, fill: "#94a3b8" },
  seriesColor: "#818cf8",
  highlightColor: "#f87171",
  ratingColor: "#34d399",
  toneColors: {
    neutral: "#94a3b8",
    info: "#38bdf8",
    success: "#34d399",
    warning: "#fbbf24",
    danger: "#f87171",
  },
};

export function useChartTheme(): ChartTheme {
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains("dark"),
  );

  useEffect(() => {
    const observer = new MutationObserver(() =>
      setIsDark(document.documentElement.classList.contains("dark")),
    );
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return isDark ? DARK_THEME : LIGHT_THEME;
}

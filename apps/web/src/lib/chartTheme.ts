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

export interface ChartTheme {
  /** Estilo del recuadro del tooltip. */
  tooltipStyle: React.CSSProperties;
  /** Color de las marcas y etiquetas de los ejes. */
  axisColor: string;
  /** Color de la serie principal (curva de evaluación, barras). */
  seriesColor: string;
  /** Color de lo que hay que destacar sobre la serie. */
  highlightColor: string;
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
  seriesColor: "#6366f1",
  highlightColor: "#ef4444",
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
  seriesColor: "#818cf8",
  highlightColor: "#f87171",
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

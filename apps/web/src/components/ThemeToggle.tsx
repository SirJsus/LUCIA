/** Conmutador de tema claro/oscuro (RF-5.6).
 *
 * Arranca con la preferencia del sistema y recuerda la elección manual en
 * `localStorage`; Tailwind está en `darkMode: "class"`, así que basta con
 * poner o quitar la clase en `<html>`.
 */
import { useEffect, useState } from "react";

const STORAGE_KEY = "lucia:theme";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  return (
    <button
      type="button"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="rounded border border-slate-300 px-2 py-1 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
      title={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}

/** Marco común de la aplicación: navegación y conmutador de tema. */
import { Link, Outlet, useMatchRoute } from "@tanstack/react-router";
import { buttonClasses } from "./styles";
import { ThemeToggle } from "./ThemeToggle";

/** `detailRoute` es la pantalla de detalle que pertenece a esa sección. Sin
 * ella, el visor de una partida no marcaba nada en la navegación mientras que
 * el tablero de análisis sí marcaba "Tableros": el enlace de Partidas apunta a
 * `/` y tiene que ser exacto, o se quedaría activo en todas las pantallas
 * (criterio C-2 de docs/07-coherencia-ui.md). */
const NAV_LINKS = [
  { to: "/", label: "Partidas", detailRoute: "/games/$gameId" },
  { to: "/boards", label: "Tableros", detailRoute: undefined },
  { to: "/stats", label: "Estadísticas", detailRoute: undefined },
  { to: "/engines", label: "Motores", detailRoute: undefined },
] as const;

export function Layout() {
  const matchRoute = useMatchRoute();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="text-lg font-bold tracking-tight">L.U.C.I.A.</span>
            <span className="hidden text-xs opacity-60 sm:inline">
              Logic &amp; Ultimate Chess Insight Algorithm
            </span>
          </Link>

          <nav className="flex gap-1">
            {NAV_LINKS.map((link) => {
              const isDetailOfThisSection =
                link.detailRoute !== undefined && matchRoute({ to: link.detailRoute });
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  activeOptions={{ exact: link.to === "/" }}
                  // El enlace activo se ve como el botón primario, y sale de la
                  // misma receta: era la última copia a mano que quedaba.
                  className={
                    isDetailOfThisSection
                      ? buttonClasses("primary")
                      : "rounded px-3 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                  }
                  activeProps={{ className: buttonClasses("primary") }}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}

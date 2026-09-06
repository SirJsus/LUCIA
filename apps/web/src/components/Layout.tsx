/** Marco común de la aplicación: navegación y conmutador de tema. */
import { Link, Outlet } from "@tanstack/react-router";
import { ThemeToggle } from "./ThemeToggle";

const NAV_LINKS = [
  { to: "/", label: "Partidas" },
  { to: "/boards", label: "Tableros" },
  { to: "/stats", label: "Estadísticas" },
  { to: "/engines", label: "Motores" },
] as const;

export function Layout() {
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
            {NAV_LINKS.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                activeOptions={{ exact: link.to === "/" }}
                className="rounded px-3 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                activeProps={{
                  className:
                    "rounded px-3 py-1.5 text-sm bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900",
                }}
              >
                {link.label}
              </Link>
            ))}
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

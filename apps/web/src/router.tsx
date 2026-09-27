/** Rutas de la aplicación (TanStack Router, definidas en código).
 *
 * Se usa el modo "code-based" en vez del basado en archivos porque son pocas
 * rutas y así no hace falta el plugin de Vite ni la generación de un árbol.
 */
import { createRootRoute, createRoute, createRouter } from "@tanstack/react-router";
import { Layout } from "./components/Layout";
import { BoardPage } from "./features/board/BoardPage";
import { BoardsPage } from "./features/board/BoardsPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { EnginesPage } from "./features/engines/EnginesPage";
import { GamesPage } from "./features/games/GamesPage";
import { DrillsPage } from "./features/training/DrillsPage";
import { PlanPage } from "./features/training/PlanPage";
import { PuzzlesPage } from "./features/training/PuzzlesPage";
import { ReplaysPage } from "./features/training/ReplaysPage";
import { SparringGamePage } from "./features/training/SparringGamePage";
import { SparringPage } from "./features/training/SparringPage";
import { GameViewerPage } from "./features/viewer/GameViewerPage";

const rootRoute = createRootRoute({ component: Layout });

const gamesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: GamesPage,
});

const gameViewerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/games/$gameId",
  component: GameViewerPage,
});

const enginesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/engines",
  component: EnginesPage,
});

const statsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/stats",
  component: DashboardPage,
});

// El plan es la portada de Entrenamiento (RF-4.5): es la pantalla que dice por
// dónde empezar, así que es donde cae quien pulsa la sección en la navegación.
const planRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training",
  component: PlanPage,
});

const puzzlesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training/puzzles",
  component: PuzzlesPage,
});

const drillsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training/drills",
  component: DrillsPage,
});

const replaysRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training/replays",
  component: ReplaysPage,
});

const sparringRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training/sparring",
  component: SparringPage,
});

const sparringGameRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training/sparring/$sparringGameId",
  component: SparringGamePage,
});

const boardsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/boards",
  component: BoardsPage,
});

const boardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/boards/$boardId",
  component: BoardPage,
});

const routeTree = rootRoute.addChildren([
  gamesRoute,
  gameViewerRoute,
  boardsRoute,
  boardRoute,
  planRoute,
  puzzlesRoute,
  drillsRoute,
  replaysRoute,
  sparringRoute,
  sparringGameRoute,
  statsRoute,
  enginesRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

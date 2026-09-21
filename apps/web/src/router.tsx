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
import { SparringGamePage } from "./features/training/SparringGamePage";
import { SparringPage } from "./features/training/SparringPage";
import { TrainingPage } from "./features/training/TrainingPage";
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

const trainingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/training",
  component: TrainingPage,
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
  trainingRoute,
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

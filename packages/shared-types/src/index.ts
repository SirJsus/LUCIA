// Tipos generados desde el OpenAPI de apps/api con `pnpm --filter @lucia/shared-types generate`.
// Hasta que exista api.d.ts, se exportan tipos manuales mínimos.

export type MoveClassification =
  | "best"
  | "excellent"
  | "good"
  | "book"
  | "inaccuracy"
  | "mistake"
  | "blunder"
  | "missed_win";

export type GamePhase = "opening" | "middlegame" | "endgame";

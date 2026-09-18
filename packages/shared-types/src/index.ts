// Tipos compartidos entre la API y el front.
//
// `api.d.ts` se genera con `make types` (vuelca el OpenAPI de apps/api y
// corre openapi-typescript). No se edita a mano. Aquí solo se re-exportan
// alias legibles, para que el front no tenga que escribir
// `components["schemas"]["..."]` en todos lados.

import type { components } from "./api";

export type { components, operations, paths } from "./api";

type Schemas = components["schemas"];

export type GameSummary = Schemas["GameSummary"];
export type GameDetail = Schemas["GameDetail"];
export type PgnImportSummary = Schemas["PgnImportSummary"];
export type AnalysisSummary = Schemas["AnalysisSummary"];
export type AnalysisDetail = Schemas["AnalysisDetail"];
export type AnalyzedMoveOut = Schemas["AnalyzedMoveOut"];
export type AnalysisRequest = Schemas["AnalysisRequest"];
export type EnginesConfigOut = Schemas["EnginesConfigOut"];
export type EngineConfigOut = Schemas["EngineConfigOut"];
export type EngineConfigUpdate = Schemas["EngineConfigUpdate"];
export type SyncSummary = Schemas["SyncSummary"];
export type PlayerStats = Schemas["PlayerStatsOut"];
export type RecordSummary = Schemas["RecordOut"];
export type TimeClassStats = Schemas["TimeClassStatsOut"];
export type OpeningStats = Schemas["OpeningStatsOut"];
export type PhaseStats = Schemas["PhaseStatsOut"];
export type MistakeTypeStats = Schemas["MistakeTypeStatsOut"];
export type TimeBucketStats = Schemas["TimeBucketStatsOut"];
export type TimeTrouble = Schemas["TimeTroubleOut"];
export type CriticalMoment = Schemas["CriticalMomentOut"];
export type MonthlyCount = Schemas["MonthlyCountOut"];
export type RepertoireComparison = Schemas["RepertoireOut"];
export type RepertoireDeparture = Schemas["DepartureOut"];
export type RepertoireRefresh = Schemas["RefreshResultOut"];
export type BoardSummary = Schemas["BoardSummary"];
export type BoardDetail = Schemas["BoardDetail"];
export type EngineLine = Schemas["EngineLineOut"];
export type AnalysisComparison = Schemas["AnalysisComparisonOut"];
export type MoveComparison = Schemas["MoveComparisonOut"];

/** Categorías de `classify_move` (lucia_core.classification). El OpenAPI las
 * expone como `string` porque en la BD se guardan así, de modo que este tipo
 * se mantiene a mano y es la fuente de verdad para la UI. */
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

/** Por qué falló una jugada (`lucia_core.insights.mistake_type`, RF-3.4). Como
 * las clasificaciones, el OpenAPI lo expone como `string` y este tipo es la
 * fuente de verdad para la UI. */
export type MistakeType = "time" | "tactical" | "endgame" | "positional";

/** Por qué una posición era crítica (`lucia_core.insights`, RF-2.8): solo
 * valía una jugada, la partida cambió de manos, o había una ganada y se
 * escapó. */
export type CriticalMomentKind = "only_move" | "swing" | "missed_chance";

/** Eventos que emite `WS /ws/analysis/{id}`. No están en el OpenAPI: el
 * esquema no describe WebSockets. */
export type AnalysisProgressEvent =
  | { status: "running"; ply: number; total: number }
  | { status: "done"; error: null }
  | { status: "error"; error: string };

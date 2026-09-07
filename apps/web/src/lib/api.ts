/** Cliente HTTP de la API de LUCIA.
 *
 * Los tipos vienen de `@lucia/shared-types`, generados desde el OpenAPI real
 * (`make types`): si un endpoint cambia de forma, esto deja de compilar en
 * vez de fallar en tiempo de ejecución.
 *
 * Vite hace de proxy: `/api/...` -> `http://localhost:8000/...` (ver
 * vite.config.ts), así que en desarrollo no hay CORS de por medio.
 */
import type {
  AnalysisComparison,
  AnalysisDetail,
  AnalysisSummary,
  BoardDetail,
  BoardSummary,
  EngineLine,
  EngineConfigUpdate,
  EnginesConfigOut,
  GameDetail,
  GameSummary,
  PlayerStats,
  SyncSummary,
} from "@lucia/shared-types";

const BASE_URL = "/api";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }
  return (await response.json()) as T;
}

/** FastAPI responde `{detail: string}` o, en errores de validación,
 * `{detail: [{loc, msg, ...}]}`. Se normalizan ambos a un texto legible. */
async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => `${(d.loc ?? []).join(".")}: ${d.msg}`).join("; ");
    }
  } catch {
    // cuerpo no-JSON (p. ej. la API caída): se cae al texto de estado
  }
  return `${response.status} ${response.statusText}`;
}

export interface GameFilters {
  username?: string;
  color?: "white" | "black";
  time_class?: string;
  rated?: boolean;
  limit?: number;
  offset?: number;
}

function toQueryString(filters: object): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const api = {
  listGames: (filters: GameFilters = {}) =>
    request<GameSummary[]>(`/games${toQueryString(filters)}`),

  getGame: (gameId: number) => request<GameDetail>(`/games/${gameId}`),

  createAnalysis: (body: {
    game_ids: number[];
    engine?: "stockfish" | "lc0";
    depth?: number | null;
    multipv?: number | null;
  }) =>
    request<AnalysisSummary[]>("/analysis", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listAnalyses: (gameId?: number) =>
    request<AnalysisSummary[]>(`/analysis${gameId === undefined ? "" : `?game_id=${gameId}`}`),

  compareAnalyses: (analysisA: number, analysisB: number) =>
    request<AnalysisComparison>(
      `/analysis/compare?analysis_a=${analysisA}&analysis_b=${analysisB}`,
    ),

  getAnalysis: (analysisId: number) => request<AnalysisDetail>(`/analysis/${analysisId}`),

  analyzePosition: (body: {
    fen: string;
    engine?: "stockfish" | "lc0";
    depth?: number | null;
    multipv?: number | null;
  }) =>
    request<EngineLine[]>("/analysis/position", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listBoards: () => request<BoardSummary[]>("/boards"),

  getBoard: (boardId: number) => request<BoardDetail>(`/boards/${boardId}`),

  createBoard: (body: {
    title: string;
    root_fen?: string;
    tree_json?: unknown;
    is_own_game?: boolean;
  }) => request<BoardDetail>("/boards", { method: "POST", body: JSON.stringify(body) }),

  updateBoard: (
    boardId: number,
    body: { title?: string; tree_json?: unknown; is_own_game?: boolean },
  ) => request<BoardDetail>(`/boards/${boardId}`, { method: "PUT", body: JSON.stringify(body) }),

  deleteBoard: async (boardId: number): Promise<void> => {
    const response = await fetch(`${BASE_URL}/boards/${boardId}`, { method: "DELETE" });
    // 204 No Content: no hay cuerpo que parsear, `request` fallaría al leerlo.
    if (!response.ok) throw new ApiError(response.status, await extractErrorMessage(response));
  },

  getStats: (username?: string) =>
    request<PlayerStats>(`/stats${username ? `?username=${encodeURIComponent(username)}` : ""}`),

  getEnginesConfig: () => request<EnginesConfigOut>("/engines/config"),

  updateEngineConfig: (engineName: string, body: EngineConfigUpdate) =>
    request<EnginesConfigOut["stockfish"]>(`/engines/config/${engineName}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  sync: (username?: string) =>
    request<SyncSummary>("/sync", {
      method: "POST",
      body: JSON.stringify({ username: username ?? null }),
    }),
};

/** URL del WebSocket de progreso. Vite proxea `/ws` al backend. */
export function analysisProgressUrl(analysisId: number): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/analysis/${analysisId}`;
}

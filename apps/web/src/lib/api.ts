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
  PgnImportSummary,
  PlayerStats,
  RepertoireComparison,
  RepertoireRefresh,
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
  return (await requestWithResponse<T>(path, init)).body;
}

/** Como `request`, pero devuelve también la respuesta HTTP: hace falta cuando
 * el dato no viene solo en el cuerpo, como el total de partidas que cumplen un
 * filtro (`X-Total-Count` en `GET /games`). */
async function requestWithResponse<T>(
  path: string,
  init?: RequestInit,
): Promise<{ body: T; response: Response }> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }
  return { body: (await response.json()) as T, response };
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

export interface GamePage {
  games: GameSummary[];
  /** Cuántas cumplen los filtros, sin contar la paginación. */
  total: number;
}

export interface GameFilters {
  username?: string;
  color?: "white" | "black";
  /** Resultado desde el punto de vista de `username`; sin él, la API lo
   * ignora, porque la misma partida es victoria para uno y derrota para el
   * otro. Lo mismo vale para `color` y `opponent`. */
  result?: "win" | "draw" | "loss";
  opponent?: string;
  /** Subcadena del nombre de la apertura: "sicilian" trae todas las
   * sicilianas. */
  opening?: string;
  time_class?: string;
  rated?: boolean;
  /** Fechas inclusivas por los dos lados, en formato `YYYY-MM-DD`. */
  since?: string;
  until?: string;
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
  /** Las partidas de una página y **cuántas cumplen los filtros en total**,
   * que es lo que permite decir "25 de 324" en vez de solo el número de
   * página. */
  listGames: async (filters: GameFilters = {}): Promise<GamePage> => {
    const { body, response } = await requestWithResponse<GameSummary[]>(
      `/games${toQueryString(filters)}`,
    );
    return { games: body, total: Number(response.headers.get("X-Total-Count") ?? body.length) };
  },

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

  getStats: (username?: string) => request<PlayerStats>(`/stats${toQueryString({ username })}`),

  /** Dónde se sale el jugador de la teoría, con lo que ya está en la caché
   * (RF-3.6). No sale a internet: eso lo hace `refreshRepertoire`. */
  getRepertoire: (username?: string) =>
    request<RepertoireComparison>(`/repertoire${toQueryString({ username })}`),

  /** Pregunta a Lichess por las posiciones que falten, hasta `budget`. Es la
   * única llamada de LUCIA que necesita red mientras se usa (ADR-0010). */
  refreshRepertoire: (username?: string) =>
    request<RepertoireRefresh>(`/repertoire/refresh${toQueryString({ username })}`, {
      method: "POST",
    }),

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

  /** Sube un archivo PGN al historial (RF-1.5).
   *
   * `playerNameInPgn` es cómo aparece el usuario dentro de ese PGN: un archivo de
   * torneo lo nombra "Durán, Jesús" y no con su usuario de chess.com.
   *
   * Va como `FormData` y no como JSON, así que **anula la cabecera
   * `Content-Type`** de `request`: el navegador tiene que poner la suya con el
   * separador de partes, o el servidor no sabe dónde empieza el archivo. */
  importPgn: (file: File, options: { username?: string; playerNameInPgn?: string } = {}) => {
    const form = new FormData();
    form.append("file", file);
    if (options.username) form.append("username", options.username);
    if (options.playerNameInPgn) form.append("player_name_in_pgn", options.playerNameInPgn);
    return request<PgnImportSummary>("/import/pgn", {
      method: "POST",
      headers: {},
      body: form,
    });
  },
};

/** URL de descarga del PGN anotado de un análisis (RF-5.5).
 *
 * Es un enlace y no una llamada `fetch`: el navegador descarga el archivo y le
 * pone el nombre que manda el servidor en `Content-Disposition`, que es
 * justamente lo que se perdería al pasarlo por JavaScript. */
export function analysisPgnUrl(analysisId: number): string {
  return `${BASE_URL}/analysis/${analysisId}/pgn`;
}

/** URL del WebSocket de progreso. Vite proxea `/ws` al backend. */
export function analysisProgressUrl(analysisId: number): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/analysis/${analysisId}`;
}

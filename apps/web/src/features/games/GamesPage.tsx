/** Lista de partidas importadas, con filtros (RF-5.3) y disparo de
 * sincronización con chess.com (RF-1). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { api, type GameFilters } from "../../lib/api";
import { formatDate, formatTimeControl, gameResult } from "../../lib/format";

const TIME_CLASSES = ["bullet", "blitz", "rapid", "daily"] as const;
const PAGE_SIZE = 25;

export function GamesPage() {
  const [filters, setFilters] = useState<GameFilters>({ limit: PAGE_SIZE, offset: 0 });
  const [syncUsername, setSyncUsername] = useState("");
  const queryClient = useQueryClient();

  const gamesQuery = useQuery({
    queryKey: ["games", filters],
    queryFn: () => api.listGames(filters),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.sync(syncUsername || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["games"] }),
  });

  function updateFilter(patch: Partial<GameFilters>) {
    // Cualquier cambio de filtro vuelve a la primera página: si estabas en la
    // página 3 y el filtro nuevo devuelve 5 resultados, verías una lista vacía.
    setFilters((current) => ({ ...current, ...patch, offset: 0 }));
  }

  const page = Math.floor((filters.offset ?? 0) / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-bold">Partidas</h1>

        <form
          className="flex items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            syncMutation.mutate();
          }}
        >
          <label className="text-sm">
            <span className="mb-1 block opacity-70">Sincronizar desde chess.com</span>
            <input
              value={syncUsername}
              onChange={(event) => setSyncUsername(event.target.value)}
              placeholder="usuario (o el de .env)"
              className="w-56 rounded border border-slate-300 bg-white px-2 py-1.5 dark:border-slate-700 dark:bg-slate-900"
            />
          </label>
          <button
            type="submit"
            disabled={syncMutation.isPending}
            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
          >
            {syncMutation.isPending ? "Sincronizando…" : "Sincronizar"}
          </button>
        </form>
      </div>

      {syncMutation.isError && <ErrorBox error={syncMutation.error} />}
      {syncMutation.isSuccess && (
        <p className="rounded border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">
          {syncMutation.data.games_upserted} partidas importadas en{" "}
          {syncMutation.data.months_synced.length} mes(es).
        </p>
      )}

      <div className="flex flex-wrap gap-3 rounded border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900">
        <label className="flex flex-col gap-1">
          <span className="opacity-70">Jugador</span>
          <input
            value={filters.username ?? ""}
            onChange={(event) => updateFilter({ username: event.target.value || undefined })}
            placeholder="cualquiera"
            className="w-44 rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-950"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="opacity-70">Color</span>
          <select
            value={filters.color ?? ""}
            onChange={(event) =>
              updateFilter({ color: (event.target.value || undefined) as GameFilters["color"] })
            }
            disabled={!filters.username}
            title={filters.username ? undefined : "Elige un jugador primero"}
            className="w-32 rounded border border-slate-300 bg-white px-2 py-1 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950"
          >
            <option value="">Ambos</option>
            <option value="white">Blancas</option>
            <option value="black">Negras</option>
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="opacity-70">Control</span>
          <select
            value={filters.time_class ?? ""}
            onChange={(event) => updateFilter({ time_class: event.target.value || undefined })}
            className="w-32 rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-950"
          >
            <option value="">Todos</option>
            {TIME_CLASSES.map((timeClass) => (
              <option key={timeClass} value={timeClass}>
                {timeClass}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="opacity-70">Puntuadas</span>
          <select
            value={filters.rated === undefined ? "" : String(filters.rated)}
            onChange={(event) =>
              updateFilter({
                rated: event.target.value === "" ? undefined : event.target.value === "true",
              })
            }
            className="w-32 rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-950"
          >
            <option value="">Todas</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </label>
      </div>

      {gamesQuery.isPending && <Spinner />}
      {gamesQuery.isError && <ErrorBox error={gamesQuery.error} onRetry={gamesQuery.refetch} />}

      {gamesQuery.data && gamesQuery.data.length === 0 && (
        <EmptyState title="No hay partidas con esos filtros">
          Si es la primera vez, sincroniza tu usuario de chess.com con el formulario de arriba.
        </EmptyState>
      )}

      {gamesQuery.data && gamesQuery.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2 font-medium">Fecha</th>
                  <th className="px-3 py-2 font-medium">Blancas</th>
                  <th className="px-3 py-2 font-medium">Negras</th>
                  <th className="px-3 py-2 font-medium">Resultado</th>
                  <th className="px-3 py-2 font-medium">Control</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {gamesQuery.data.map((game) => (
                  <tr
                    key={game.id}
                    className="border-t border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
                  >
                    <td className="whitespace-nowrap px-3 py-2 opacity-70">
                      {formatDate(game.played_at)}
                    </td>
                    <td className="px-3 py-2">
                      {game.white_username}{" "}
                      <span className="opacity-60">({game.white_rating})</span>
                    </td>
                    <td className="px-3 py-2">
                      {game.black_username}{" "}
                      <span className="opacity-60">({game.black_rating})</span>
                    </td>
                    <td className="px-3 py-2 font-mono">{gameResult(game)}</td>
                    <td className="whitespace-nowrap px-3 py-2 opacity-70">
                      {formatTimeControl(game.time_control)}{" "}
                      <span className="opacity-70">{game.time_class}</span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        to="/games/$gameId"
                        params={{ gameId: String(game.id) }}
                        className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                      >
                        Analizar
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <button
              type="button"
              disabled={(filters.offset ?? 0) === 0}
              onClick={() =>
                setFilters((current) => ({
                  ...current,
                  offset: Math.max(0, (current.offset ?? 0) - PAGE_SIZE),
                }))
              }
              className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40 dark:border-slate-700"
            >
              ← Anterior
            </button>
            <span className="opacity-70">Página {page}</span>
            <button
              type="button"
              disabled={gamesQuery.data.length < PAGE_SIZE}
              onClick={() =>
                setFilters((current) => ({
                  ...current,
                  offset: (current.offset ?? 0) + PAGE_SIZE,
                }))
              }
              className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40 dark:border-slate-700"
            >
              Siguiente →
            </button>
          </div>
        </>
      )}
    </div>
  );
}

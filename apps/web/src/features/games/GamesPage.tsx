/** Lista de partidas importadas, con filtros (RF-5.3) y disparo de
 * sincronización con chess.com (RF-1). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner, SuccessBox } from "../../components/Feedback";
import { buttonClasses, FIELD_CLASSES, PANEL_CLASSES } from "../../components/styles";
import { api, type GameFilters } from "../../lib/api";
import { formatDate, formatTimeClass, formatTimeControl, gameResult } from "../../lib/format";

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
              className={`w-56 ${FIELD_CLASSES}`}
            />
          </label>
          <Button type="submit" variant="primary" disabled={syncMutation.isPending}>
            {syncMutation.isPending ? "Sincronizando…" : "Sincronizar"}
          </Button>
        </form>
      </div>

      {syncMutation.isError && <ErrorBox error={syncMutation.error} />}
      {syncMutation.isSuccess && (
        <SuccessBox>
          {syncMutation.data.games_upserted} partidas importadas en{" "}
          {syncMutation.data.months_synced.length} mes(es).
        </SuccessBox>
      )}

      <div className={`flex flex-wrap gap-3 p-3 text-sm ${PANEL_CLASSES}`}>
        <label className="flex flex-col gap-1">
          <span className="opacity-70">Jugador</span>
          <input
            value={filters.username ?? ""}
            onChange={(event) => updateFilter({ username: event.target.value || undefined })}
            placeholder="cualquiera"
            className={`w-44 ${FIELD_CLASSES}`}
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
            className={`w-32 disabled:opacity-50 ${FIELD_CLASSES}`}
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
            className={`w-32 ${FIELD_CLASSES}`}
          >
            <option value="">Todos</option>
            {TIME_CLASSES.map((timeClass) => (
              <option key={timeClass} value={timeClass}>
                {formatTimeClass(timeClass)}
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
            className={`w-32 ${FIELD_CLASSES}`}
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
                      <span className="opacity-70">{formatTimeClass(game.time_class)}</span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        to="/games/$gameId"
                        params={{ gameId: String(game.id) }}
                        className={buttonClasses("secondary", "sm")}
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
            <Button
              size="sm"
              disabled={(filters.offset ?? 0) === 0}
              onClick={() =>
                setFilters((current) => ({
                  ...current,
                  offset: Math.max(0, (current.offset ?? 0) - PAGE_SIZE),
                }))
              }
            >
              ← Anterior
            </Button>
            <span className="opacity-70">Página {page}</span>
            <Button
              size="sm"
              disabled={gamesQuery.data.length < PAGE_SIZE}
              onClick={() =>
                setFilters((current) => ({
                  ...current,
                  offset: (current.offset ?? 0) + PAGE_SIZE,
                }))
              }
            >
              Siguiente →
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

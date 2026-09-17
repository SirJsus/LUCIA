/** Lista de partidas importadas, con filtros (RF-5.3) y disparo de
 * sincronización con chess.com (RF-1). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "../../components/Button";
import { CustomPositionBadge } from "../../components/CustomPositionBadge";
import { FieldLabel } from "../../components/FieldLabel";
import { EmptyState, ErrorBox, Spinner, SuccessBox } from "../../components/Feedback";
import { DataTable } from "../../components/DataTable";
import { FilterBar, FilterSelect, FilterText } from "../../components/FilterBar";
import {
  buttonClasses,
  FIELD_CLASSES,
  TABLE_CELL_CLASSES,
  TABLE_ROW_CLASSES,
} from "../../components/styles";
import { api, type GameFilters } from "../../lib/api";
import { formatDate, formatTimeClass, formatTimeControl, gameResult } from "../../lib/format";

const TIME_CLASSES = ["bullet", "blitz", "rapid", "daily"] as const;

/** Por qué hay tres filtros deshabilitados. Se dice una vez en la barra y no
 * en cada campo: es el mismo motivo, y repetirlo tres veces es ruido. En un
 * `title` no valdría —con teclado no aparece nunca— y estos campos, además,
 * no se pueden ni tabular estando deshabilitados (criterios C-1 y C-3 de
 * docs/07-coherencia-ui.md). */
const PLAYER_FIRST_HINT =
  "Color, resultado y rival necesitan un jugador: la misma partida es victoria para uno y derrota para el otro.";

/** Las dos fechas son inclusivas, y se dice con las mismas palabras en las
 * dos: "desde el 1" y "hasta el 31" cubren el 1 y el 31 enteros. */
const DATE_HINT = "Incluye el día indicado";
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
  // Todo lo que hay en `filters` menos la paginación, que no filtra nada.
  const hasFilters = Object.entries(filters).some(
    ([key, value]) => key !== "limit" && key !== "offset" && value !== undefined,
  );

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
          <FieldLabel label="Sincronizar desde chess.com">
            <input
              value={syncUsername}
              onChange={(event) => setSyncUsername(event.target.value)}
              placeholder="usuario (o el de .env)"
              className={`w-56 ${FIELD_CLASSES}`}
            />
          </FieldLabel>
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

      <FilterBar>
        <FilterText
          label="Jugador"
          value={filters.username ?? ""}
          onChange={(username) => updateFilter({ username: username || undefined })}
          placeholder="cualquiera"
          width="w-44"
        />

        {/* Color, resultado y rival dependen de quién sea el jugador: la misma
            partida es victoria para uno y derrota para el otro. Sin jugador la
            API los ignora, y aquí se deshabilitan para que no parezca que
            filtran (criterio C-3). */}
        <FilterSelect
          label="Color"
          value={filters.color ?? ""}
          onChange={(color) => updateFilter({ color: (color || undefined) as GameFilters["color"] })}
          options={[
            ["", "Ambos"],
            ["white", "Blancas"],
            ["black", "Negras"],
          ]}
          disabled={!filters.username}
        />

        <FilterSelect
          label="Resultado"
          value={filters.result ?? ""}
          onChange={(result) =>
            updateFilter({ result: (result || undefined) as GameFilters["result"] })
          }
          options={[
            ["", "Todos"],
            ["win", "Victorias"],
            ["draw", "Tablas"],
            ["loss", "Derrotas"],
          ]}
          disabled={!filters.username}
        />

        <FilterText
          label="Rival"
          value={filters.opponent ?? ""}
          onChange={(opponent) => updateFilter({ opponent: opponent || undefined })}
          placeholder="cualquiera"
          disabled={!filters.username}
        />

        <FilterText
          label="Apertura"
          value={filters.opening ?? ""}
          onChange={(opening) => updateFilter({ opening: opening || undefined })}
          placeholder="p. ej. siciliana"
          hint="Busca por parte del nombre: «sicilian» trae todas las sicilianas"
          width="w-48"
        />

        {/* Las dos fechas incluyen el día que se escribe en ellas, que es lo
            que hace la API; sin decirlo, "hasta el 31" se lee igual de bien
            como "hasta la medianoche del 31" (criterio C-6). */}
        <FilterText
          label="Desde"
          type="date"
          value={filters.since ?? ""}
          onChange={(since) => updateFilter({ since: since || undefined })}
          hint={DATE_HINT}
        />

        <FilterText
          label="Hasta"
          type="date"
          value={filters.until ?? ""}
          onChange={(until) => updateFilter({ until: until || undefined })}
          hint={DATE_HINT}
        />

        <FilterSelect
          label="Control"
          value={filters.time_class ?? ""}
          onChange={(timeClass) => updateFilter({ time_class: timeClass || undefined })}
          options={[
            ["", "Todos"],
            ...TIME_CLASSES.map((timeClass) => [timeClass, formatTimeClass(timeClass)] as const),
          ]}
        />

        <FilterSelect
          label="Puntuadas"
          value={filters.rated === undefined ? "" : String(filters.rated)}
          onChange={(rated) =>
            updateFilter({ rated: rated === "" ? undefined : rated === "true" })
          }
          options={[
            ["", "Todas"],
            ["true", "Sí"],
            ["false", "No"],
          ]}
        />
        {!filters.username && (
          <p className="w-full text-xs opacity-60">{PLAYER_FIRST_HINT}</p>
        )}
      </FilterBar>

      {gamesQuery.isPending && <Spinner />}
      {gamesQuery.isError && <ErrorBox error={gamesQuery.error} onRetry={gamesQuery.refetch} />}

      {gamesQuery.data && gamesQuery.data.games.length === 0 && (
        // Con nueve filtros, un vacío casi siempre es cosa de uno de ellos, y
        // con ninguno puesto nunca lo es: decir "con esos filtros" cuando no
        // hay filtros manda a buscar lo que no existe (criterio C-3).
        <EmptyState
          title={hasFilters ? "No hay partidas con esos filtros" : "Todavía no hay partidas"}
        >
          {hasFilters
            ? "Prueba a quitar alguno: el rango de fechas y la apertura son los que más recortan."
            : "Sincroniza tu usuario de chess.com con el formulario de arriba."}
        </EmptyState>
      )}

      {gamesQuery.data && gamesQuery.data.games.length > 0 && (
        <>
          <DataTable headers={["Fecha", "Blancas", "Negras", "Resultado", "Control", ""]}>
            {gamesQuery.data.games.map((game) => (
              <tr key={game.id} className={TABLE_ROW_CLASSES}>
                <td className={`whitespace-nowrap opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {formatDate(game.played_at)}
                </td>
                <td className={TABLE_CELL_CLASSES}>
                  {game.white_username} <span className="opacity-60">({game.white_rating})</span>
                  {game.starts_from_custom_position && (
                    <span className="ml-1.5">
                      <CustomPositionBadge />
                    </span>
                  )}
                </td>
                <td className={TABLE_CELL_CLASSES}>
                  {game.black_username} <span className="opacity-60">({game.black_rating})</span>
                </td>
                <td className={`font-mono ${TABLE_CELL_CLASSES}`}>{gameResult(game)}</td>
                <td className={`whitespace-nowrap opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {formatTimeControl(game.time_control)}{" "}
                  <span className="opacity-70">{formatTimeClass(game.time_class)}</span>
                </td>
                <td className={`text-right ${TABLE_CELL_CLASSES}`}>
                  <Link
                    to="/games/$gameId"
                    params={{ gameId: String(game.id) }}
                    className={buttonClasses("secondary", "sm")}
                  >
                    Ver partida
                  </Link>
                </td>
              </tr>
            ))}
          </DataTable>

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
            {/* Cuántas se ven de cuántas cumplen el filtro: solo el número de
                página no dice si el filtro dejó fuera media colección
                (criterio C-3). */}
            <span className="opacity-70">
              Página {page} · {gamesQuery.data.games.length} de {gamesQuery.data.total} partidas
            </span>
            <Button
              size="sm"
              disabled={gamesQuery.data.games.length < PAGE_SIZE}
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

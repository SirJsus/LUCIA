/** Lista de partidas importadas, con filtros (RF-5.3) y las dos formas de
 * traer partidas: sincronizar con chess.com (RF-1.2) e importar un archivo
 * PGN de otra fuente —OTB, lichess— (RF-1.5). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { Button } from "../../components/Button";
import { CustomPositionBadge } from "../../components/CustomPositionBadge";
import { GameSourceBadge } from "../../components/GameSourceBadge";
import { FieldLabel } from "../../components/FieldLabel";
import { EmptyState, ErrorBox, Spinner, SuccessBox, WarningBox } from "../../components/Feedback";
import { DataTable } from "../../components/DataTable";
import { FilterBar, FilterSelect, FilterText } from "../../components/FilterBar";
import {
  buttonClasses,
  FIELD_CLASSES,
  TABLE_CELL_CLASSES,
  TABLE_ROW_CLASSES,
} from "../../components/styles";
import type { PgnImportSummary } from "@lucia/shared-types";
import { api, type GameFilters } from "../../lib/api";
import {
  formatDate,
  formatRating,
  formatTimeClass,
  formatTimeControl,
  gameResult,
} from "../../lib/format";

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

/** Por qué se pregunta el nombre al importar un PGN. Un archivo de torneo
 * nombra al jugador "Durán, Jesús" y no con su usuario de chess.com, y el
 * dashboard y los filtros de esta misma pantalla casan por nombre: sin
 * decirlo, la partida se guarda pero no cuenta en ningún marcador. */
const PLAYER_NAME_IN_PGN_HINT =
  "Como apareces en ese archivo; si no, la partida no cuenta en tus estadísticas.";
const PAGE_SIZE = 25;

/** Cuántas partidas traía el archivo importado: las guardadas más las que se
 * saltaron. La API no lo manda como tal porque es la suma de lo que ya
 * devuelve, y tenerlo dos veces daría dos sitios donde descuadrar. */
function countGamesInFile(summary: PgnImportSummary): number {
  return (
    summary.games_imported + summary.games_already_present + summary.skipped_game_reasons.length
  );
}

export function GamesPage() {
  const [filters, setFilters] = useState<GameFilters>({ limit: PAGE_SIZE, offset: 0 });
  const [syncUsername, setSyncUsername] = useState("");
  const [playerNameInPgn, setPlayerNameInPgn] = useState("");
  // El archivo no puede vivir en el estado de React como los demás campos: un
  // `<input type="file">` no admite `value`, así que se lee del elemento al
  // enviar y se vacía por la misma vía al terminar.
  const pgnFileInput = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const gamesQuery = useQuery({
    queryKey: ["games", filters],
    queryFn: () => api.listGames(filters),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.sync(syncUsername || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["games"] }),
  });

  const importPgnMutation = useMutation({
    mutationFn: (file: File) =>
      // Sin `username`: las partidas se atribuyen a CHESSCOM_USERNAME, el
      // mismo jugador del que habla el dashboard. El campo de al lado es el
      // usuario **al que se sincroniza**, y gobernar con él a quién pertenece
      // un PGN importado sería un acoplamiento que no se ve en pantalla.
      api.importPgn(file, { playerNameInPgn }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["games"] });
      if (pgnFileInput.current) pgnFileInput.current.value = "";
    },
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
      {/* El título va en su propia línea y los dos formularios en la de abajo,
          alineados por su base. Antes los tres se repartían una sola fila con
          `justify-between`: al envolverse en una ventana estrecha, el título se
          quedaba solo arriba y las dos formas de traer partidas acababan a
          distinta altura, cuando son lo mismo y se leen juntas (fila 65 del
          inventario de docs/07-coherencia-ui.md, criterio C-2). */}
      <div className="space-y-3">
        <h1 className="text-2xl font-bold">Partidas</h1>

        <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
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

          {/* Segunda vía para traer partidas: un archivo PGN de otra fuente
              (RF-1.5). Va junto a "Sincronizar" y no en otra pantalla porque las
              dos hacen lo mismo —llenar este listado— y se esperan en el mismo
              sitio (criterio C-2 de docs/07-coherencia-ui.md). */}
          <form
            className="flex items-end gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              const file = pgnFileInput.current?.files?.[0];
              if (file) importPgnMutation.mutate(file);
            }}
          >
            <FieldLabel label="Importar PGN (OTB, lichess)">
              <input
                ref={pgnFileInput}
                type="file"
                // Sin `required`, pulsar "Importar" sin archivo no hacía nada ni
                // decía por qué; con él, el navegador lo pide (criterio C-3).
                required
                accept=".pgn,application/x-chess-pgn,text/plain"
                className={`w-64 ${FIELD_CLASSES} file:mr-2 file:rounded file:border-0 file:bg-slate-200 file:px-2 file:py-0.5 file:text-xs dark:file:bg-slate-700 dark:file:text-slate-100`}
              />
            </FieldLabel>
            <FieldLabel label="Mi nombre en el PGN" hint={PLAYER_NAME_IN_PGN_HINT}>
              <input
                value={playerNameInPgn}
                onChange={(event) => setPlayerNameInPgn(event.target.value)}
                placeholder="Durán, Jesús"
                className={`w-44 ${FIELD_CLASSES}`}
              />
            </FieldLabel>
            {/* Secundario: la acción principal de la pantalla es
                "Sincronizar", y solo hay una por pantalla
                (components/Button.tsx). */}
            <Button type="submit" disabled={importPgnMutation.isPending}>
              {importPgnMutation.isPending ? "Importando…" : "Importar"}
            </Button>
          </form>
        </div>
      </div>

      {syncMutation.isError && <ErrorBox error={syncMutation.error} />}
      {syncMutation.isSuccess && (
        <SuccessBox>
          {syncMutation.data.games_upserted} partidas sincronizadas en{" "}
          {syncMutation.data.months_synced.length} mes(es).
        </SuccessBox>
      )}

      {importPgnMutation.isError && <ErrorBox error={importPgnMutation.error} />}
      {importPgnMutation.isSuccess && (
        // "3 de 13": el total del archivo va en la misma frase que lo guardado,
        // porque una importación parcial contada en dos recuadros —el verde y
        // el ámbar de abajo— obliga a sumar para saber si salió bien (C-3).
        <SuccessBox>
          {importPgnMutation.data.games_imported} de {countGamesInFile(importPgnMutation.data)}{" "}
          partidas del archivo importadas
          {importPgnMutation.data.games_already_present > 0 &&
            `; ${importPgnMutation.data.games_already_present} ya estaban en el historial`}
          .
        </SuccessBox>
      )}
      {/* Reconocer al jugador es lo que hace que la partida cuente en el
          dashboard y en los filtros por color, resultado y rival. Si no se
          reconoció en ninguna, el recuadro verde de arriba sería un éxito
          engañoso: la partida está guardada y no sale en ningún marcador, y
          sin decirlo aquí se descubre días después (C-3). */}
      {importPgnMutation.isSuccess &&
        importPgnMutation.data.games_matched_to_player === 0 &&
        importPgnMutation.data.games_imported + importPgnMutation.data.games_already_present > 0 && (
          <WarningBox>
            No te reconocí en ninguna: revisa «Mi nombre en el PGN», tiene que estar escrito igual
            que en el archivo. Las partidas están guardadas, pero no cuentan en tus estadísticas.
          </WarningBox>
        )}
      {/* Las partidas que el archivo traía y no se pudieron guardar se
          enumeran con su motivo: un recuento de "importadas" que no cuadra con
          lo que tenía el archivo, sin decir por qué, se lee como un fallo
          (criterio C-3). */}
      {importPgnMutation.isSuccess && importPgnMutation.data.skipped_game_reasons.length > 0 && (
        <WarningBox>
          <p className="font-medium">
            {importPgnMutation.data.skipped_game_reasons.length} partidas del archivo no se importaron:
          </p>
          <ul className="mt-1 list-inside list-disc opacity-90">
            {importPgnMutation.data.skipped_game_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </WarningBox>
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
            : "Sincroniza tu usuario de chess.com o importa un archivo PGN con los formularios de arriba."}
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
                  {game.white_username}{" "}
                  <span className="opacity-60">({formatRating(game.white_rating)})</span>
                  {/* Las dos insignias van con las blancas, que es la primera
                      columna con nombre: son propiedades de la partida entera,
                      no de un bando, y repetirlas en las dos columnas las haría
                      parecer del jugador (criterio C-6). */}
                  <span className="ml-1.5 inline-flex gap-1">
                    <GameSourceBadge platform={game.platform} />
                    {game.starts_from_custom_position && <CustomPositionBadge />}
                  </span>
                </td>
                <td className={TABLE_CELL_CLASSES}>
                  {game.black_username}{" "}
                  <span className="opacity-60">({formatRating(game.black_rating)})</span>
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

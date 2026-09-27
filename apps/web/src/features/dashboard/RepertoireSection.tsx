/** Dónde se sale el repertorio propio de la teoría de maestros (RF-3.6).
 *
 * La comparación se lee de lo que LUCIA ya preguntó al Opening Explorer de
 * Lichess; preguntar por lo que falta es un botón aparte, porque es la única
 * parte de la aplicación que necesita conexión mientras se usa (ADR-0010). Por
 * eso la sección dice siempre **cuánto sabe y cuánto le falta**: una
 * comparación a medias que no se anuncia es peor que ninguna (criterio C-3 de
 * docs/07-coherencia-ui.md).
 *
 * Las posiciones se preguntan de una en una y espaciadas, para no abusar de un
 * servicio gratuito ajeno, así que completar el historial la primera vez lleva
 * varias pulsaciones, y por eso cada consulta dice cuántas posiciones trajo y
 * cuántas quedan en vez de dejar la petición colgada minutos.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { DataTable } from "../../components/DataTable";
import {
  EmptyState,
  ErrorBox,
  ProgressBox,
  Spinner,
  SuccessBox,
  WarningBox,
} from "../../components/Feedback";
import { RecordBadges } from "../../components/RecordBadges";
import { TABLE_CELL_CLASSES, TABLE_ROW_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatPercent } from "../../lib/format";
import { moveNumberLabel } from "../../lib/moves";

/** El mismo encabezado abreviado que las otras dos tablas del panel: la
 * puntuación se lee con el marcador al lado, no sola. */
const RECORD_HEADER = <abbr title="Victorias / Tablas / Derrotas">V/T/D</abbr>;

export function RepertoireSection({ username }: { username: string }) {
  const queryClient = useQueryClient();

  const repertoireQuery = useQuery({
    queryKey: ["repertoire", username],
    queryFn: () => api.getRepertoire(username || undefined),
  });

  const refreshMutation = useMutation({
    mutationFn: () => api.refreshRepertoire(username || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["repertoire", username] }),
  });

  if (repertoireQuery.isPending) return <Spinner label="Cargando el repertorio…" />;
  if (repertoireQuery.isError) {
    return <ErrorBox error={repertoireQuery.error} onRetry={repertoireQuery.refetch} />;
  }

  const {
    departures,
    games_compared,
    positions_known,
    positions_missing,
    explorer_token_configured,
    positions_per_refresh,
    seconds_between_positions,
  } = repertoireQuery.data;
  const isComplete = positions_missing === 0;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="primary"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending || isComplete || !explorer_token_configured}
          title={
            !explorer_token_configured
              ? "Falta el token de Lichess"
              : isComplete
                ? "No falta ninguna posición por consultar"
                : `Trae hasta ${positions_per_refresh} posiciones, alrededor de ${Math.round(positions_per_refresh * seconds_between_positions)} segundos`
          }
        >
          {refreshMutation.isPending ? "Consultando a Lichess…" : "Consultar a Lichess"}
        </Button>
        {/* Sobre qué está hecha la comparación, en los dos estados y con los
            mismos datos: cuántas partidas se miraron y de cuántas posiciones se
            sabe teoría. */}
        <p className="text-xs opacity-60">
          Comparadas {games_compared} partidas con la teoría de {positions_known} posiciones.
          {isComplete && " No falta ninguna por consultar."}
        </p>
      </div>

      {/* Que la comparación esté a medias no es letra pequeña: cambia lo que
          significa la tabla de abajo, así que se dice con el mismo recuadro de
          aviso que el resto de la aplicación (criterios C-3 y C-4). */}
      {/* Sin token no se puede consultar nada, así que se dice antes de que el
          usuario pulse y no después, con un error (criterio C-3). */}
      {!explorer_token_configured && (
        <WarningBox>
          Falta el token de Lichess. El Opening Explorer dejó de admitir peticiones anónimas, así
          que hace falta uno para traer la teoría: es gratuito y no necesita permisos especiales.
          Sácalo en{" "}
          <a
            className="underline"
            href="https://lichess.org/account/oauth/token"
            target="_blank"
            rel="noreferrer"
          >
            lichess.org/account/oauth/token
          </a>{" "}
          y ponlo en <code>LICHESS_TOKEN</code>, en tu <code>.env</code>. Lo que ya esté
          consultado se sigue viendo sin él.
        </WarningBox>
      )}

      {explorer_token_configured && !isComplete && !refreshMutation.isPending && (
        <WarningBox>
          La comparación está a medias: faltan {positions_missing} posiciones por preguntarle a
          Lichess, así que puede haber jugadas tuyas fuera de la teoría que todavía no aparezcan.
          Se preguntan de una en una y espaciadas, para no abusar de un servicio gratuito ajeno,
          así que puede hacer falta pulsar «Consultar a Lichess» varias veces; cada una trae hasta{" "}
          {positions_per_refresh}.
        </WarningBox>
      )}

      {refreshMutation.isPending && (
        <ProgressBox
          label="Preguntando a la base de maestros…"
          detail={`hasta ${positions_per_refresh} posiciones, una cada ${seconds_between_positions} s`}
          progress={null}
        />
      )}
      {refreshMutation.isError && <ErrorBox error={refreshMutation.error} />}
      {/* Qué consiguió la consulta, como ya hace sincronizar en Partidas, que es
          la otra acción de LUCIA que sale a internet (criterios C-2 y C-3). */}
      {refreshMutation.isSuccess && (
        <SuccessBox>
          {refreshMutation.data.fetched} posiciones consultadas a Lichess.{" "}
          {refreshMutation.data.remaining === 0
            ? "No queda ninguna: la comparación ya está completa."
            : `Quedan ${refreshMutation.data.remaining} por consultar.`}
        </SuccessBox>
      )}

      {departures.length === 0 ? (
        // El vacío de una comparación completa y el de una que aún no se ha
        // hecho no son el mismo (criterio C-3): con el mismo título, "no hay
        // comparación" contradecía a "ninguna de tus partidas se sale".
        <EmptyState
          title={isComplete ? "Nada fuera de la teoría" : "Todavía no hay comparación"}
        >
          {isComplete
            ? "Ninguna de tus partidas se sale de la teoría en las primeras jugadas."
            : "Pulsa «Consultar a Lichess» para traer la teoría de tus aperturas."}
        </EmptyState>
      ) : (
        <>
          <DataTable
            headers={[
              "Jugada",
              "Juegas",
              "Los maestros juegan",
              "Color",
              "Partidas",
              RECORD_HEADER,
              "Puntuación",
            ]}
          >
            {departures.map((departure) => (
              <tr
                key={`${departure.color}-${departure.ply}-${departure.san}`}
                className={TABLE_ROW_CLASSES}
              >
                <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {moveNumberLabel(departure.ply)}
                </td>
                <td className={`font-mono ${TABLE_CELL_CLASSES}`}>{departure.san}</td>
                <td className={TABLE_CELL_CLASSES}>
                  <span className="flex flex-wrap gap-1">
                    {departure.master_moves.map((masterMove) => (
                      <Badge key={masterMove} tone="info">
                        {masterMove}
                      </Badge>
                    ))}
                  </span>
                </td>
                <td className={`opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {departure.color === "white" ? "Blancas" : "Negras"}
                </td>
                <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {departure.games}
                </td>
                <td className={TABLE_CELL_CLASSES}>
                  <RecordBadges record={departure} />
                </td>
                <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
                  {formatPercent(departure.score_percent, 1)}
                </td>
              </tr>
            ))}
          </DataTable>
          <p className="text-xs opacity-60">
            Cada fila es la primera jugada tuya que ya no está en la base de maestros, con lo que
            se juega en su lugar —de la más jugada a la menos— y cómo te fue después. Salirse de
            la teoría no es un error: lo que dice algo es la puntuación que sacas cuando lo haces.
          </p>
        </>
      )}
    </div>
  );
}

/** Sparring (RF-4.3): elegir rival y empezar, o retomar una partida.
 *
 * Es la antesala; jugar está en `SparringGamePage`. Se parte en dos pantallas
 * porque una partida vive en la base de datos y tiene URL propia
 * (`/training/sparring/$sparringGameId`): cerrar la pestaña a mitad y volver
 * después es lo normal cuando una partida dura veinte minutos, igual que pasa
 * con los tableros de análisis.
 *
 * Elegir rival, bando y fuerza es `SparringSetupForm`, compartido con las
 * otras dos pantallas desde las que se abre una partida —la lista de
 * "re-jugar" y el visor (RF-4.4)—: aquí solo se dice cómo se llama el botón.
 *
 * El listado es el de **todas** las partidas contra el motor, empezadas desde
 * cero o retomadas: son la misma cosa y viven en la misma tabla (ADR-0020),
 * así que las retomadas se distinguen con una insignia y no con otra lista.
 */
import type { SparringGame } from "@lucia/shared-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { Badge } from "../../components/Badge";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { buttonClasses } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { outcomeFor, outcomeSentence } from "./sparring";
import { SparringSetupForm, type SparringSetup } from "./SparringSetupForm";
import { TrainingHeader } from "./TrainingHeader";

export const SPARRING_GAMES_QUERY_KEY = ["sparring", "games"] as const;

export function SparringPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const gamesQuery = useQuery({
    queryKey: SPARRING_GAMES_QUERY_KEY,
    queryFn: api.getSparringGames,
  });

  const startMutation = useMutation({
    mutationFn: (setup: SparringSetup) => api.startSparringGame(setup),
    onSuccess: (game) => {
      queryClient.invalidateQueries({ queryKey: SPARRING_GAMES_QUERY_KEY });
      navigate({
        to: "/training/sparring/$sparringGameId",
        params: { sparringGameId: String(game.id) },
      });
    },
  });

  const games = gamesQuery.data ?? [];
  const unfinishedGames = games.filter((game) => game.result === null);

  return (
    <div className="space-y-6">
      <TrainingHeader>
        Partidas contra el motor con la fuerza que tú le pongas. No cuentan en tus estadísticas: un
        rival al que se le ha bajado la fuerza no dice nada de tu rendimiento real.
      </TrainingHeader>

      <Panel title="Nueva partida">
        <SparringSetupForm
          submitLabel="Empezar partida"
          pendingLabel="Abriendo partida…"
          isPending={startMutation.isPending}
          onSubmit={(setup) => startMutation.mutate(setup)}
        />
      </Panel>

      {startMutation.isError && <ErrorBox error={startMutation.error} />}

      {gamesQuery.isPending && <Spinner label="Cargando tus partidas de sparring…" />}
      {gamesQuery.isError && <ErrorBox error={gamesQuery.error} onRetry={gamesQuery.refetch} />}

      {gamesQuery.isSuccess && games.length === 0 && (
        <EmptyState title="Todavía no has jugado ninguna">
          Elige color y rival ahí arriba y pulsa «Empezar partida».
        </EmptyState>
      )}

      {games.length > 0 && (
        <Panel
          title="Tus partidas"
          aside={
            unfinishedGames.length > 0 ? (
              <Badge tone="info">{unfinishedGames.length} sin terminar</Badge>
            ) : undefined
          }
          bodyClassName=""
        >
          <ul>
            {games.map((game) => (
              <SparringGameRow key={game.id} game={game} />
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}

function SparringGameRow({ game }: { game: SparringGame }) {
  const outcome = outcomeFor(game);
  return (
    <li className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-3 py-2 text-sm last:border-b-0 dark:border-slate-800">
      <span className="font-medium">
        {game.player_color === "white" ? "Blancas" : "Negras"} contra {game.opponent_name}
      </span>
      {/* Una partida retomada empieza a mitad, y sin decirlo el listado no
          distingue una cosa de la otra (RF-4.4). */}
      {game.origin_game_id !== null && <Badge tone="neutral">re-jugada</Badge>}
      {/* El resultado dicho en palabras y no solo como marcador: "0-1" no
          comunica nada a quien no lo lee (criterio C-6). */}
      {outcome === null ? (
        <Badge tone="info">en curso</Badge>
      ) : (
        <span className="opacity-70">{outcomeSentence(game)}</span>
      )}
      <span className="ml-auto text-xs opacity-60">{formatDate(game.created_at)}</span>
      <Link
        to="/training/sparring/$sparringGameId"
        params={{ sparringGameId: String(game.id) }}
        className={buttonClasses("secondary", "sm")}
      >
        {outcome === null ? "Seguir jugando" : "Ver partida"}
      </Link>
    </li>
  );
}

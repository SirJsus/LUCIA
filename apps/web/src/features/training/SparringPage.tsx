/** Sparring (RF-4.3): elegir rival y empezar, o retomar una partida.
 *
 * Es la antesala; jugar está en `SparringGamePage`. Se parte en dos pantallas
 * porque una partida vive en la base de datos y tiene URL propia
 * (`/training/sparring/$sparringGameId`): cerrar la pestaña a mitad y volver
 * después es lo normal cuando una partida dura veinte minutos, igual que pasa
 * con los tableros de análisis.
 *
 * **Las dos perillas de fuerza no son la misma**, y la pantalla lo dice en vez
 * de fingir que sí: Stockfish acepta un Elo, y Lc0 con una red Maia no —su
 * fuerza es la de la red— pero a cambio juega como una persona. Ver
 * `apps/api/lucia_api/services/sparring.py`.
 */
import type { SparringGame } from "@lucia/shared-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { FieldLabel } from "../../components/FieldLabel";
import { Panel } from "../../components/Panel";
import { buttonClasses, FIELD_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate, formatEngineName } from "../../lib/format";
import { outcomeFor, outcomeSentence } from "./sparring";
import { TrainingHeader } from "./TrainingHeader";

export const SPARRING_GAMES_QUERY_KEY = ["sparring", "games"] as const;

/** El Elo que trae el formulario. No es el de nadie en concreto: es el punto
 * medio del rango que acepta Stockfish redondeado a un número que se entiende,
 * y desde ahí se sube o se baja. */
const DEFAULT_ENGINE_ELO = 1500;

/** Los topes de `UCI_Elo` en Stockfish. Repetidos aquí y en
 * `services/sparring.py::STOCKFISH_ELO_RANGE` porque el deslizador necesita
 * sus extremos antes de preguntar nada; el servidor los vuelve a comprobar, y
 * es el suyo el que manda. */
const MIN_ENGINE_ELO = 1320;
const MAX_ENGINE_ELO = 3190;

export function SparringPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [playerColor, setPlayerColor] = useState<"white" | "black">("white");
  const [engine, setEngine] = useState<"stockfish" | "lc0">("stockfish");
  const [engineElo, setEngineElo] = useState(DEFAULT_ENGINE_ELO);

  const gamesQuery = useQuery({
    queryKey: SPARRING_GAMES_QUERY_KEY,
    queryFn: api.getSparringGames,
  });

  const startMutation = useMutation({
    mutationFn: () =>
      api.startSparringGame({
        player_color: playerColor,
        engine,
        engine_elo: engine === "stockfish" ? engineElo : null,
      }),
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
        {/* Es un `<form>` y no un `<div>` con un botón para que se envíe con
            Intro, como los otros formularios de escritura de la aplicación
            —sincronizar e importar PGN en Partidas, crear tablero, partida
            propia, configurar motores— (criterio C-1, la misma razón que cerró
            la fila 86). */}
        <form
          className="flex flex-wrap items-start gap-4 text-sm"
          onSubmit={(event) => {
            event.preventDefault();
            startMutation.mutate();
          }}
        >
          <FieldLabel label="Juegas con" hint="El motor lleva el otro color.">
            <select
              className={FIELD_CLASSES}
              value={playerColor}
              onChange={(event) => setPlayerColor(event.target.value as "white" | "black")}
            >
              <option value="white">Blancas</option>
              <option value="black">Negras</option>
            </select>
          </FieldLabel>

          <FieldLabel
            label="Rival"
            hint={
              engine === "stockfish"
                ? "Juega bien y se contiene hasta el Elo que le pidas."
                : "Red Maia: imita a una persona de ~1500, con sus errores, no los de un motor."
            }
          >
            <select
              className={FIELD_CLASSES}
              value={engine}
              onChange={(event) => setEngine(event.target.value as "stockfish" | "lc0")}
            >
              <option value="stockfish">{formatEngineName("stockfish")}</option>
              <option value="lc0">{formatEngineName("lc0")} · Maia</option>
            </select>
          </FieldLabel>

          {/* Con Lc0 no hay Elo que elegir, así que el control no se queda
              desactivado —un control muerto invita a pelearse con él— sino que
              se sustituye por lo que ocupa su lugar: cuál es su fuerza. */}
          {engine === "stockfish" ? (
            <FieldLabel
              label={`Fuerza: ${engineElo} Elo`}
              hint={`Entre ${MIN_ENGINE_ELO} y ${MAX_ENGINE_ELO}.`}
            >
              <input
                type="range"
                className="w-48"
                min={MIN_ENGINE_ELO}
                max={MAX_ENGINE_ELO}
                step={10}
                value={engineElo}
                onChange={(event) => setEngineElo(Number(event.target.value))}
              />
            </FieldLabel>
          ) : (
            <FieldLabel label="Fuerza" hint="La de la red; no se puede pedir otra.">
              <span className="py-1.5">~1500 Elo</span>
            </FieldLabel>
          )}

          <div className="self-end">
            <Button type="submit" variant="primary" disabled={startMutation.isPending}>
              {startMutation.isPending ? "Abriendo partida…" : "Empezar partida"}
            </Button>
          </div>
        </form>
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

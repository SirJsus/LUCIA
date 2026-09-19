/** Marcar un tablero como "partida propia" (RF-6.5).
 *
 * Un tablero no cuenta en el dashboard ni en los patrones salvo que el
 * usuario diga que esa partida la jugó él. Decirlo no es un interruptor: el
 * tablero no sabe contra quién se jugó, de qué color, cómo acabó ni qué día,
 * y esas cuatro cosas son justo las que las estadísticas necesitan para
 * contarlo sin inventar nada. Por eso aquí hay un formulario y no una casilla.
 *
 * De dónde salen los datos y adónde van: lo que se escribe aquí viaja a
 * `PUT /boards/{id}/own-game` junto con el PGN del árbol (`tree.ts::toPgn`),
 * y el servidor publica el tablero como una fila del historial. A partir de
 * ahí sale en Partidas, en el marcador, en las aperturas y en los patrones
 * como cualquier otra (ver `services/own_games.py`).
 */
import { useMutation } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import type { BoardDetail, OwnGameLink } from "@lucia/shared-types";

import { Button } from "../../components/Button";
import { ErrorBox, WarningBox } from "../../components/Feedback";
import { FieldLabel } from "../../components/FieldLabel";
import { Panel } from "../../components/Panel";
import { buttonClasses, FIELD_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";

type PlayerColor = OwnGameLink["player_color"];
type PlayerResult = OwnGameLink["result"];

// Los mismos nombres que los filtros «Color» y «Resultado» de Partidas, en
// singular porque aquí se habla de una partida y no de un montón: el mismo
// dato no puede llamarse de dos maneras en dos pantallas (criterio C-2 de
// docs/07-coherencia-ui.md).
const PLAYER_COLOR_LABELS: Record<PlayerColor, string> = { white: "Blancas", black: "Negras" };
const PLAYER_RESULT_LABELS: Record<PlayerResult, string> = {
  win: "Victoria",
  draw: "Tablas",
  loss: "Derrota",
};

interface OwnGameForm {
  player_color: PlayerColor;
  opponent_name: string;
  result: PlayerResult;
  played_on: string;
  /** A quién se le atribuye. No es un campo del formulario: se conserva el de
   * la partida ya publicada para que corregir un dato no la reatribuya al
   * usuario de la configuración. Vacío al marcar por primera vez, que es
   * cuando la API resuelve `CHESSCOM_USERNAME`. */
  username: string | null;
}

function buildOwnGameForm(ownGame: OwnGameLink | null): OwnGameForm {
  return {
    player_color: ownGame?.player_color ?? "white",
    opponent_name: ownGame?.opponent_name ?? "",
    // Sin valor previo no se elige ninguno por defecto que suene bien:
    // "Victoria" precargada haría que una partida perdida se guardara como
    // ganada con solo no mirar el campo.
    result: ownGame?.result ?? "draw",
    played_on: ownGame?.played_on ?? new Date().toISOString().slice(0, 10),
    username: ownGame?.username ?? null,
  };
}

/** La línea que va en la cabecera del tablero, junto al título: dice si este
 * tablero cuenta y abre el formulario. */
export function OwnGameStatus({
  ownGame,
  isEditing,
  onToggleEditing,
}: {
  ownGame: OwnGameLink | null;
  isEditing: boolean;
  onToggleEditing: () => void;
}) {
  return (
    <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
      {/* "Estadísticas" es como se llama la pantalla en la barra de
          navegación: decirlo aquí "dashboard" sería un segundo nombre para
          el mismo sitio (criterio C-2). */}
      <span className={ownGame ? "" : "opacity-60"}>
        {ownGame
          ? `Partida propia: cuenta en tus Estadísticas (${PLAYER_COLOR_LABELS[ownGame.player_color]} contra ${ownGame.opponent_name}, ${PLAYER_RESULT_LABELS[ownGame.result].toLowerCase()}, ${formatDate(ownGame.played_on)})`
          : "Este tablero no cuenta en tus Estadísticas"}
      </span>
      {/* El estado del tablero se enseña siempre y la acción está al lado,
          en vez de esconder una de las dos: es la misma forma que tienen el
          resto de propiedades del tablero (criterio C-3). */}
      <Button size="sm" onClick={onToggleEditing}>
        {isEditing
          ? "Cancelar"
          : ownGame
            ? "Corregir los datos"
            : "Marcar como partida propia"}
      </Button>
      {/* Abrir una partida se llama "Ver partida" y se ve como un botón en
          las dos pantallas que llevan a ella; hacerlo aquí con otro nombre y
          con aspecto de texto suelto sería una tercera forma (criterio
          C-2). */}
      {ownGame && (
        <Link
          to="/games/$gameId"
          params={{ gameId: String(ownGame.game_id) }}
          className={buttonClasses("secondary", "sm")}
        >
          Ver partida
        </Link>
      )}
    </div>
  );
}

/** El formulario con los cuatro datos que el tablero no tiene. */
export function OwnGamePanel({
  boardId,
  ownGame,
  pgn,
  hasMoves,
  onSaved,
}: {
  boardId: number;
  ownGame: OwnGameLink | null;
  /** El árbol de ahora en PGN: es lo que se publica como partida. */
  pgn: string;
  hasMoves: boolean;
  onSaved: (board: BoardDetail) => void;
}) {
  const [form, setForm] = useState<OwnGameForm>(() => buildOwnGameForm(ownGame));

  const publishMutation = useMutation({
    mutationFn: () => api.publishOwnGame(boardId, { ...form, pgn }),
    onSuccess: onSaved,
  });
  const withdrawMutation = useMutation({
    mutationFn: () => api.withdrawOwnGame(boardId),
    onSuccess: onSaved,
  });
  const isSaving = publishMutation.isPending || withdrawMutation.isPending;

  return (
    <Panel title="Partida propia">
      {/* Un `<form>` de verdad, como los de sincronizar, importar PGN, crear
          tablero y configurar motores: Intro desde cualquier campo guarda, y
          quien va con teclado no tiene que llegar hasta el botón (criterio
          C-1 de docs/07-coherencia-ui.md). */}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          publishMutation.mutate();
        }}
      >
      <div className="flex flex-wrap items-end gap-3 text-sm">
        <FieldLabel label="Color">
          <select
            value={form.player_color}
            onChange={(event) =>
              setForm({ ...form, player_color: event.target.value as PlayerColor })
            }
            className={FIELD_CLASSES}
          >
            {Object.entries(PLAYER_COLOR_LABELS).map(([color, label]) => (
              <option key={color} value={color}>
                {label}
              </option>
            ))}
          </select>
        </FieldLabel>
        <FieldLabel label="Rival">
          <input
            value={form.opponent_name}
            onChange={(event) => setForm({ ...form, opponent_name: event.target.value })}
            placeholder="Nombre del rival"
            className={FIELD_CLASSES}
          />
        </FieldLabel>
        <FieldLabel label="Resultado">
          <select
            value={form.result}
            onChange={(event) => setForm({ ...form, result: event.target.value as PlayerResult })}
            className={FIELD_CLASSES}
          >
            {Object.entries(PLAYER_RESULT_LABELS).map(([result, label]) => (
              <option key={result} value={result}>
                {label}
              </option>
            ))}
          </select>
        </FieldLabel>
        <FieldLabel label="Fecha">
          <input
            type="date"
            value={form.played_on}
            onChange={(event) => setForm({ ...form, played_on: event.target.value })}
            className={FIELD_CLASSES}
          />
        </FieldLabel>
      </div>

      {/* Lo que va a pasar al pulsar, antes de pulsar: publicar mete la
          partida en el historial, y eso se nota en el dashboard (criterio
          C-3). Lo que no se puede saber tampoco se promete. */}
      <div className="mt-2">
        {/* Las dos pantallas se nombran como se llaman en la barra de
            navegación, y el hueco del control de tiempo se nombra como se ve
            —«—», lo que devuelve `formatTimeClass` para `unknown`— en vez de
            inventarle una tercera forma de decirlo (criterios C-2 y C-5). */}
        <WarningBox>
          La línea principal de este tablero se guardará como una partida más: saldrá en Partidas y
          contará en tus Estadísticas como cualquier otra. No se le puede poner rating ni control de
          tiempo —un tablero no los sabe—, así que los dos saldrán con el hueco «—», como en las
          partidas importadas de un PGN.
        </WarningBox>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        {/* Secundaria: la acción principal de la pantalla es «Analizar» y
            solo hay una por pantalla (components/Button.tsx), la misma regla
            por la que «Importar» tampoco la es. */}
        <Button
          type="submit"
          disabled={form.opponent_name.trim() === "" || !hasMoves || isSaving}
          title={
            hasMoves
              ? undefined
              : "Añade alguna jugada a la línea principal: una partida sin jugadas no cuenta nada"
          }
        >
          {/* "Marcar como partida propia" es el nombre del botón que abre
              este panel (`OwnGameStatus`): repetirlo aquí daría el mismo
              texto a dos acciones distintas —abrir el formulario y
              enviarlo—, que es lo que C-2 prohíbe en el otro sentido. El que
              envía se llama igual marque por primera vez o corrija. */}
          {publishMutation.isPending ? "Guardando…" : "Guardar los datos"}
        </Button>
        {ownGame && (
          /* Preguntar antes, como al eliminar un tablero o una variante:
             esto saca una partida del historial y de las estadísticas, y la
             consecuencia se dice en la pregunta y no en un `title` que con
             teclado no aparece nunca (criterios C-2 y C-3). */
          <Button
            variant="danger"
            onClick={() => {
              const opponent = ownGame.opponent_name;
              if (
                window.confirm(
                  `¿Quitar la marca de partida propia? La partida contra ${opponent} se irá de Partidas y dejará de contar en tus Estadísticas. El tablero se queda entero.`,
                )
              ) {
                withdrawMutation.mutate();
              }
            }}
            disabled={isSaving}
          >
            {withdrawMutation.isPending ? "Quitando…" : "Quitar la marca"}
          </Button>
        )}
      </div>

      {/* El motivo de un control deshabilitado se enseña, no se esconde en un
          `title` que con teclado no aparece (criterio C-3). */}
      {!hasMoves && (
        <p className="mt-2 text-xs opacity-60">
          Una partida propia necesita jugadas: añade alguna a la línea principal.
        </p>
      )}
      {form.opponent_name.trim() === "" && hasMoves && (
        <p className="mt-2 text-xs opacity-60">
          Falta el nombre del rival: es por donde el filtro «Rival» de Partidas la encuentra.
        </p>
      )}
      {publishMutation.isError && <ErrorBox error={publishMutation.error} />}
      {withdrawMutation.isError && <ErrorBox error={withdrawMutation.error} />}
      </form>
    </Panel>
  );
}

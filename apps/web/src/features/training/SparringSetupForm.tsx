/** Elegir rival y bando antes de jugar contra el motor (RF-4.3, RF-4.4).
 *
 * Lo usan las tres pantallas desde las que se abre una partida —la antesala
 * de Sparring, la lista de "re-jugar desde el error" y el visor de una partida
 * propia—, para que elegir la dificultad se haga igual en todas: mismos
 * controles, mismo orden y mismas explicaciones (criterio C-2 de
 * docs/07-coherencia-ui.md).
 *
 * **Las dos perillas de fuerza no son la misma**, y el formulario lo dice en
 * vez de fingir que sí: Stockfish acepta un Elo y se contiene hasta él; Lc0
 * con una red Maia no se contiene —imita a una persona de ~1500— y su fuerza
 * es la de la red, así que ahí no hay nada que elegir. Por eso con Lc0 el
 * deslizador no se queda desactivado —un control muerto invita a pelearse con
 * él— sino que se sustituye por lo que ocupa su lugar. Ver
 * `apps/api/lucia_api/services/sparring.py`.
 */
import type { SparringGameCreate } from "@lucia/shared-types";
import { useState } from "react";
import { Button } from "../../components/Button";
import { FieldLabel } from "../../components/FieldLabel";
import { FIELD_CLASSES } from "../../components/styles";
import { formatOpponentName } from "../../lib/format";

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

/** Lo que el formulario deja elegir, que es todo lo que hace falta para abrir
 * una partida menos de dónde se retoma (`origin`), que lo pone quien llama. */
export type SparringSetup = Pick<SparringGameCreate, "player_color" | "engine" | "engine_elo">;

export function SparringSetupForm({
  defaultPlayerColor = "white",
  submitLabel,
  pendingLabel,
  isPending,
  onSubmit,
}: {
  /** El bando que se ofrece de entrada. Retomando una partida propia es el que
   * se jugaba (RF-4.4); en una partida nueva, blancas. Se puede cambiar. */
  defaultPlayerColor?: "white" | "black";
  submitLabel: string;
  pendingLabel: string;
  isPending: boolean;
  onSubmit: (setup: SparringSetup) => void;
}) {
  const [playerColor, setPlayerColor] = useState<"white" | "black">(defaultPlayerColor);
  const [engine, setEngine] = useState<"stockfish" | "lc0">("stockfish");
  const [engineElo, setEngineElo] = useState(DEFAULT_ENGINE_ELO);

  return (
    // Es un `<form>` y no un `<div>` con un botón para que se envíe con Intro,
    // como los otros formularios de escritura de la aplicación (criterio C-1,
    // la misma razón que cerró la fila 86).
    <form
      className="flex flex-wrap items-start gap-4 text-sm"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit({
          player_color: playerColor,
          engine,
          engine_elo: engine === "stockfish" ? engineElo : null,
        });
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
          <option value="stockfish">{formatOpponentName("stockfish")}</option>
          <option value="lc0">{formatOpponentName("lc0")}</option>
        </select>
      </FieldLabel>

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
        <Button type="submit" variant="primary" disabled={isPending}>
          {isPending ? pendingLabel : submitLabel}
        </Button>
      </div>
    </form>
  );
}

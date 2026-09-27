/** Las líneas del motor, en columnas: evaluación y continuación propuesta.
 *
 * La comparten el panel del motor del tablero de análisis (RF-6.2) y las
 * alternativas de una jugada en el visor (RF-10.2). Es el mismo dato —las N
 * mejores líneas de una posición— así que se lee igual en los dos sitios
 * (criterio C-5 de docs/07-coherencia-ui.md); lo único que cambia es qué pasa
 * al pulsar una jugada, porque el tablero de análisis puede jugarla y el visor
 * de una partida terminada no.
 *
 * Señalar la jugada n de una línea, con ratón o con el tabulador, dibuja sus n
 * primeras jugadas sobre el tablero: sin eso hay que reconstruir "Cf3 d5 c4 e6"
 * mentalmente, que es justo lo que no puede hacer quien todavía no lee bien una
 * variante. Pulsar hace lo mismo, que es la única vía que queda en una pantalla
 * táctil.
 */
import type { EngineLine } from "@lucia/shared-types";
import { formatScore } from "../../lib/score";
import { Badge } from "../Badge";
import { WdlBar } from "../WdlBar";
import { MoveButton } from "./MoveButton";

/** Cuántas jugadas de cada línea se enseñan. Más allá, la continuación deja de
 * ser información y pasa a ser ruido. */
const MAX_SHOWN_MOVES = 12;

export function EngineLineList({
  lines,
  onPreviewLine,
  onPlayLine,
  playedUci,
}: {
  lines: EngineLine[];
  /** Jugada que se jugó de verdad desde esta posición, si se sabe: la línea que
   * empieza por ella se marca. Sin la marca, en el visor no se distingue la
   * jugada de la partida de las que solo propone el motor. */
  playedUci?: string;
  /** Continuación a dibujar en el tablero, o `null` para dejar de dibujarla. */
  onPreviewLine: (pvUci: string[] | null) => void;
  /** Jugar la línea hasta la jugada pulsada. Si no se pasa, pulsar dibuja esa
   * continuación en el tablero, que es lo único que puede hacer el visor. */
  onPlayLine?: (sanMoves: string[]) => void;
}) {
  const canPlayLines = onPlayLine !== undefined;
  // La W/D/L la contesta el motor y no siempre está (RF-2.6): con Stockfish y
  // Lc0 sí, con otro motor UCI puede que no, y los análisis guardados antes de
  // pedírsela tampoco la traen.
  const showsWdl = lines.some((line) => line.wdl);

  return (
    <>
      <div className="flex gap-2 border-b border-slate-200 px-3 py-1.5 text-xs opacity-60 dark:border-slate-800">
        <span className="w-14 shrink-0">Evaluación</span>
        {/* La columna solo se anuncia si hay algo debajo: un motor que no
            informe W/D/L, o un análisis anterior a que se le pidiera, dejaría
            el encabezado prometiendo una columna vacía (criterio C-3). */}
        {showsWdl && <span className="w-24 shrink-0">Gana / tablas / pierde</span>}
        <span>
          Línea propuesta · pulsa una jugada para{" "}
          {canPlayLines ? "llevar el tablero hasta ahí" : "verla sobre el tablero"}
        </span>
      </div>
      <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
        {lines.map((line) => (
          <li
            key={line.rank}
            className="flex gap-2 px-3 py-2"
            onMouseLeave={() => onPreviewLine(null)}
            onBlur={() => onPreviewLine(null)}
          >
            <span
              className="w-14 shrink-0 font-mono tabular-nums"
              title="Ventaja en peones desde el punto de vista de las blancas"
            >
              {formatScore(line)}
            </span>
            {showsWdl && (
              <span className="w-24 shrink-0">{line.wdl && <WdlBar wdl={line.wdl} />}</span>
            )}
            <span className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
              {line.pv_san.slice(0, MAX_SHOWN_MOVES).map((san, index) => {
                const previewUpToHere = () => onPreviewLine(line.pv_uci.slice(0, index + 1));
                return (
                  <MoveButton
                    key={`${line.rank}-${index}`}
                    onClick={() =>
                      onPlayLine ? onPlayLine(line.pv_san.slice(0, index + 1)) : previewUpToHere()
                    }
                    onMouseEnter={previewUpToHere}
                    onFocus={previewUpToHere}
                    title={
                      canPlayLines
                        ? `Jugar la línea hasta ${san}`
                        : `Ver la línea hasta ${san} sobre el tablero`
                    }
                    className="px-0.5"
                  >
                    {san}
                  </MoveButton>
                );
              })}
              {line.pv_uci[0] === playedUci && (
                <Badge tone="info" title="Es la jugada que se jugó en la partida">
                  la que jugaste
                </Badge>
              )}
            </span>
          </li>
        ))}
      </ul>
    </>
  );
}

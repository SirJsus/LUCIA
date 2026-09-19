/** Líneas del motor para la posición actual (RF-6.2), con evaluación desde el
 * punto de vista de las blancas, como es costumbre en ajedrez.
 *
 * Lo propio de este panel son los **estados** del motor —apagado, buscando,
 * con error, sin líneas y con líneas—, porque es la pantalla que más depende
 * de él (criterio C-3 de docs/07-coherencia-ui.md). Las líneas en sí las pinta
 * `EngineLineList`, que comparte con el visor: es el mismo dato, y desde
 * RF-10.2 el visor también lo enseña.
 */
import type { EngineLine } from "@lucia/shared-types";
import { EmptyState, ErrorBox, ProgressBox } from "../../components/Feedback";
import { EngineLineList } from "../../components/board/EngineLineList";
import { Panel } from "../../components/Panel";
import { formatEngineName } from "../../lib/format";

export function EngineLines({
  lines,
  engineName,
  isEngineOn,
  isLoading,
  error,
  onPlayLine,
  onPreviewLine,
}: {
  lines: EngineLine[] | undefined;
  /** Qué motor firma estas líneas: sin decirlo, dos evaluaciones distintas de
   * la misma posición no se pueden comparar (criterio C-5). */
  engineName: string;
  isEngineOn: boolean;
  isLoading: boolean;
  error: unknown;
  /** Jugadas (SAN) a jugar desde la posición actual, en orden. */
  onPlayLine: (sanMoves: string[]) => void;
  /** Continuación a dibujar en el tablero, o `null` para dejar de dibujarla. */
  onPreviewLine: (pvUci: string[] | null) => void;
}) {
  // Qué le pasa al motor ahora mismo, si es que hay algo que contar. El panel
  // se quedaba fuera de la pantalla al apagarlo, y "no hay panel" se confunde
  // con "el motor no dice nada".
  const status = !isEngineOn ? (
    <EmptyState title="Motor apagado">
      Enciéndelo en la cabecera para ver qué jugadas propone aquí.
    </EmptyState>
  ) : isLoading ? (
    <ProgressBox label="Analizando la posición…" progress={null} />
  ) : error ? (
    <ErrorBox error={error} />
  ) : !lines?.length ? (
    <EmptyState title="Sin líneas para esta posición">
      El motor no propone ninguna jugada aquí.
    </EmptyState>
  ) : null;

  return (
    <Panel title={`Motor · ${formatEngineName(engineName)}`} bodyClassName="">
      {status && <div className="p-3">{status}</div>}

      {isEngineOn && !!lines?.length && (
        <EngineLineList lines={lines} onPreviewLine={onPreviewLine} onPlayLine={onPlayLine} />
      )}
    </Panel>
  );
}

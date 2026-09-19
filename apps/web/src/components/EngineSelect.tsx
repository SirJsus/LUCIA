/** Elegir con qué motor se analiza.
 *
 * Estaba copiado entero —valor, `onChange`, clases y opciones— en el visor y
 * en el tablero de análisis, con dos textos de ayuda distintos y los nombres
 * "Stockfish" y "Lc0" escritos a mano, saltándose `formatEngineName`
 * (criterios C-2 y C-5 de docs/07-coherencia-ui.md).
 */
import { ENGINE_IDS, formatEngineName, type EngineId } from "../lib/format";
import { FIELD_CLASSES } from "./styles";

const LABEL = "Motor con el que analizar";

export function EngineSelect({
  value,
  onChange,
}: {
  value: EngineId;
  onChange: (engine: EngineId) => void;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value as EngineId)}
      title={LABEL}
      aria-label={LABEL}
      className={`text-sm ${FIELD_CLASSES}`}
    >
      {ENGINE_IDS.map((engine) => (
        <option key={engine} value={engine}>
          {formatEngineName(engine)}
        </option>
      ))}
    </select>
  );
}

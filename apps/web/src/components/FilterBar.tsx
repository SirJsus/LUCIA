/** La barra de filtros: la caja y los campos que van dentro.
 *
 * Los campos de Partidas y de Estadísticas repetían a mano la misma receta
 * —etiqueta en `opacity-70`, control con `FIELD_CLASSES`, `disabled:opacity-50`
 * y el motivo en `title`—, así que dos filtros equivalentes podían verse
 * distintos según la pantalla (criterio C-2 de docs/07-coherencia-ui.md).
 *
 * Los campos de texto **esperan a que se deje de teclear** antes de avisar:
 * escribir "sicilian" mandaba ocho peticiones, y el mismo filtro ya esperaba
 * en Estadísticas y no en Partidas. La espera vive aquí para que sea la misma
 * en las dos.
 */
import { useEffect, useState, type ReactNode } from "react";
import { FieldLabel } from "./FieldLabel";
import { FIELD_CLASSES, PANEL_CLASSES } from "./styles";

/** Cuánto se espera desde la última tecla antes de aplicar un filtro escrito. */
const TYPING_DELAY_MS = 400;

export function FilterBar({ children }: { children: ReactNode }) {
  return (
    <div className={`flex flex-wrap items-start gap-3 p-3 text-sm ${PANEL_CLASSES}`}>
      {children}
    </div>
  );
}

interface FilterFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  /** Qué hay que saber para usar el campo: que la apertura busca por parte del
   * nombre, que la fecha incluye el día. Se enseña **debajo**, como los campos
   * de la pantalla de motores: en un `title` solo lo ve quien pasa el ratón
   * (criterio C-6). */
  hint?: string;
  disabled?: boolean;
  /** Ancho del control, en clases de Tailwind. */
  width?: string;
}

export function FilterText({
  label,
  value,
  onChange,
  hint,
  disabled,
  width = "w-40",
  type = "text",
  placeholder,
}: FilterFieldProps & { type?: "text" | "date"; placeholder?: string }) {
  const [typed, setTyped] = useState(value);

  // El valor de fuera manda cuando cambia por otra vía (limpiar filtros, otra
  // pantalla): sin esto el campo se quedaría con lo último tecleado.
  useEffect(() => setTyped(value), [value]);

  useEffect(() => {
    if (typed === value) return;
    const timer = setTimeout(() => onChange(typed), TYPING_DELAY_MS);
    return () => clearTimeout(timer);
    // `onChange` cambia en cada render de la pantalla; incluirlo reiniciaría
    // la espera continuamente y el filtro no llegaría a aplicarse nunca.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typed, value]);

  return (
    <FieldLabel label={label} hint={hint}>
      <input
        type={type}
        value={typed}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(event) => setTyped(event.target.value)}
        className={`${width} disabled:cursor-not-allowed disabled:opacity-50 ${FIELD_CLASSES}`}
      />
    </FieldLabel>
  );
}

export function FilterSelect({
  label,
  value,
  onChange,
  options,
  hint,
  disabled,
  width = "w-32",
}: FilterFieldProps & {
  /** Cada opción, como `[valor, texto]`; la primera suele ser la de "todas". */
  options: readonly (readonly [string, string])[];
}) {
  return (
    <FieldLabel label={label} hint={hint}>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className={`${width} disabled:cursor-not-allowed disabled:opacity-50 ${FIELD_CLASSES}`}
      >
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </FieldLabel>
  );
}

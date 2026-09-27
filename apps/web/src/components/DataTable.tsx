/** Tabla de datos: cabecera gris, filas separadas por una línea.
 *
 * Las tres tablas de la aplicación —partidas, control de tiempo y aperturas—
 * repetían copiada la misma receta de `table`/`thead`/`th`. Hoy coincidían
 * carácter a carácter; nada garantizaba que la cuarta lo hiciera (criterio C-2
 * de docs/07-coherencia-ui.md). Las clases de fila y celda viven en
 * `styles.ts`, porque las escribe quien pinta cada fila.
 */
import type { ReactNode } from "react";
import { Panel } from "./Panel";

export function DataTable({
  headers,
  children,
}: {
  /** Encabezados de columna, en orden. Una cadena vacía deja la columna sin
   * título, que es lo que quiere la de acciones. */
  headers: ReactNode[];
  children: ReactNode;
}) {
  return (
    <Panel bodyClassName="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left dark:bg-slate-800">
          <tr>
            {headers.map((header, index) => (
              <th key={index} className="px-3 py-2 font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </Panel>
  );
}

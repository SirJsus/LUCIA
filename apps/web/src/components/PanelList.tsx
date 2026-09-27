/** Listado de filas dentro de un panel: la forma con la que la aplicación
 * enseña una lista que no es tabular del todo.
 *
 * Existe por lo mismo que `DataTable`: la receta —un `Panel` con el cuerpo sin
 * relleno, una `<ul>` dentro y filas separadas por una línea— estaba escrita a
 * mano en el listado de partidas de sparring (RF-4.3) y copiada carácter a
 * carácter en el de errores que re-jugar (RF-4.4), incluidas las clases del
 * `<li>` y el `ml-auto` de la fecha. Dos listas iguales sostenidas a mano son
 * dos listas que divergen a la tercera (fila 95 del inventario de
 * docs/07-coherencia-ui.md, criterio C-2).
 *
 * **No sustituye a `DataTable`**, que es para lo que sí es una tabla —columnas
 * con encabezado, como Partidas—. Aquí cada fila es una frase con sus piezas y
 * puede desplegarse: la de re-jugar abre debajo el formulario de dificultad.
 *
 * Las clases de la fila viven en `styles.ts` y no aquí, por lo mismo que las de
 * `DataTable`: las escribe quien pinta cada fila.
 */
import type { ReactNode } from "react";
import { Panel } from "./Panel";

export function PanelList({
  title,
  aside,
  children,
}: {
  title: ReactNode;
  /** Lo que va a la derecha del título, normalmente cuántas quedan. */
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Panel title={title} aside={aside} bodyClassName="">
      <ul>{children}</ul>
    </Panel>
  );
}

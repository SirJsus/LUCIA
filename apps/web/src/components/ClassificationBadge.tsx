/** Insignia de la clasificación de una jugada (RF-2.2): "??", "★", "?!"…
 *
 * Su receta estaba copiada en tres pantallas, con un tamaño de letra fuera de
 * la escala de Tailwind. Además el símbolo iba solo, con el nombre escondido
 * en un `title`: aquí el nombre viaja siempre como texto accesible, para que
 * "??" no dependa de saberse la notación ni del color de fondo (criterios C-6
 * y C-7 de docs/07-coherencia-ui.md).
 */
import { Badge } from "./Badge";
import { classificationStyle } from "../lib/classification";

export function ClassificationBadge({
  classification,
  detail,
}: {
  classification: string;
  /** Lo que se añade al nombre en el texto emergente ("precisión 92.4 %"). */
  detail?: string;
}) {
  const style = classificationStyle(classification);
  const description = detail ? `${style.label} · ${detail}` : style.label;

  return (
    <Badge title={description} className={style.className}>
      <span aria-hidden="true">{style.symbol}</span>
      <span className="sr-only">{description}</span>
    </Badge>
  );
}

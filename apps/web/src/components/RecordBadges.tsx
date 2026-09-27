/** Victorias, tablas y derrotas de un marcador.
 *
 * Cada número lleva su letra: los tres se distinguían solo por el color de
 * fondo, que no es una diferencia para quien no los ve (criterio C-7 de
 * docs/07-coherencia-ui.md).
 *
 * Vive en `components/` desde que lo usan tres tablas —control de tiempo,
 * apertura y salidas de la teoría—: es el mismo dato y se lee igual en las
 * tres (C-2). Acepta cualquier cosa con las tres cifras, porque el marcador de
 * las salidas de teoría no es un `RecordSummary` de la API sino tres campos
 * sueltos de la misma respuesta.
 */
import { Badge, type BadgeTone } from "./Badge";

export function RecordBadges({
  record,
}: {
  record: { wins: number; draws: number; losses: number };
}) {
  return (
    <span className="flex gap-1">
      <RecordBadge count={record.wins} letter="V" name="victorias" tone="success" />
      <RecordBadge count={record.draws} letter="T" name="tablas" tone="neutral" />
      <RecordBadge count={record.losses} letter="D" name="derrotas" tone="danger" />
    </span>
  );
}

function RecordBadge({
  count,
  letter,
  name,
  tone,
}: {
  count: number;
  letter: string;
  name: string;
  tone: BadgeTone;
}) {
  return (
    <Badge tone={tone} title={`${count} ${name}`}>
      <span className="tabular-nums">{count}</span> {letter}
    </Badge>
  );
}

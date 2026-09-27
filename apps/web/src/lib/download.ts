/** Guardar un texto como archivo desde el navegador.
 *
 * Hace falta desde que la exportación del PGN anotado (RF-5.5) dejó de ser un
 * `<a download>` apuntando a la API: con el enlace, la descarga la hacía el
 * navegador y un error del servidor se guardaba como si fuera el archivo, sin
 * que la pantalla dijera nada (fila 70 del inventario de
 * docs/07-coherencia-ui.md). Ahora la respuesta se pide, se comprueba y solo si
 * está bien se guarda, que es lo que hace esta función.
 *
 * El `URL.revokeObjectURL` no es opcional: sin él, cada descarga deja en memoria
 * una copia del archivo mientras la pestaña siga abierta. Pero **se difiere un
 * tick a propósito**: revocarlo en la misma vuelta del bucle de eventos que el
 * `click()` llega a cancelar la descarga en algunos navegadores, que todavía no
 * han empezado a leer el blob cuando la URL deja de ser válida.
 */
export function saveTextAsFile(filename: string, text: string, mediaType: string): void {
  const blobUrl = URL.createObjectURL(new Blob([text], { type: mediaType }));
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 0);
}

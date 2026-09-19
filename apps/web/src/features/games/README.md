# `features/games`

Lista de partidas importadas con filtros y paginación (RF-5.3) y las dos formas
de traer partidas: sincronizar con chess.com (RF-1.2) e importar un archivo PGN
de otra fuente —OTB, lichess— (RF-1.5). Desde aquí se entra al visor
([`features/viewer`](../viewer/README.md)).

Los dos formularios viven juntos en la cabecera porque hacen lo mismo, llenar
este listado, y quien busca uno busca el otro (criterio C-2). La acción
principal sigue siendo "Sincronizar"; "Importar" es secundaria.

**Importar PGN.** El archivo no cabe en el estado de React —un `<input
type="file">` no admite `value`—, así que se lee de una ref al enviar y se
vacía por la misma vía al terminar. El campo "Mi nombre en el PGN" es lo que
hace que la partida cuente: un archivo de torneo nombra al jugador "Durán,
Jesús" y no con su usuario, y el dashboard y tres de los filtros de esta misma
pantalla casan por nombre. De ahí los tres avisos posibles tras importar:
cuántas de las que traía el archivo se guardaron, que no se reconoció al
usuario en ninguna (guardadas, pero sin contar en ningún marcador) y qué
partidas se quedaron fuera y por qué. El total del archivo se compone aquí
—guardadas más ya presentes más saltadas— y no es un campo de la API: es la
suma de lo que ya devuelve. El porqué de cada decisión está en
[ADR-0011](../../../../../docs/adr/0011-pgn-manual-en-la-misma-tabla.md).

Una partida importada llega con huecos donde el PGN no decía nada —los dos
ratings, el control de tiempo y el ritmo—, y la tabla los enseña como "—" con
`formatRating`, `formatTimeControl` y `formatTimeClass` de `lib/format.ts`, el
mismo hueco que la precisión sin analizar (criterio C-5).

La tabla sale de `components/DataTable`, y se entra a una partida por el enlace
"Ver partida" del final de la fila: es la misma forma que el listado de
tableros ([`features/board`](../board/README.md)), y el motivo de que sea un
enlace con aspecto de botón y no una fila pulsable es que así se puede abrir en
otra pestaña y se ve dónde hay que pulsar (criterio C-2 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)).

Los nueve filtros salen de `components/FilterBar` —los mismos campos que
Estadísticas— y viajan tal cual a `GET /games`. Tres de ellos, **color,
resultado y rival, necesitan un jugador**: la misma partida es victoria para uno
y derrota para el otro, así que sin `username` el servidor los ignora y la
pantalla los enseña deshabilitados con el motivo escrito en la barra (no en un
`title`, que con teclado no aparece). La apertura busca por parte del nombre y
las dos fechas incluyen el día que se indica; los campos de texto esperan a que
se deje de teclear antes de consultar. El porqué de cada decisión está en la
nota de RF-5.3 de
[`docs/02-requerimientos.md`](../../../../../docs/02-requerimientos.md).

La paginación dice "Página N · 25 de 324 partidas": el total sale de la cabecera
`X-Total-Count` de `GET /games`, y sin él no se sabría si el filtro dejó fuera
media colección.

Las partidas que no empiezan en la posición estándar se marcan con
`CustomPositionBadge`, a partir del campo `starts_from_custom_position` que
trae `GET /games`; el visor hace lo mismo en su cabecera.

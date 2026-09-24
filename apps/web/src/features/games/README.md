# `features/games`

Lista de partidas importadas con filtros y paginación (RF-5.3), las dos formas
de traer partidas —sincronizar con chess.com (RF-1.2) e importar un archivo PGN
de otra fuente, OTB o lichess (RF-1.5)— y el **análisis en lote** (RF-2.5), que
solo se pide desde aquí. Desde aquí se entra también al visor
([`features/viewer`](../viewer/README.md)), que es donde se analiza de una en
una.

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

**Analizar en lote** (RF-2.5). Las casillas de la primera columna componen la
tanda y la barra sobre la tabla elige **un** motor para todas
(`components/EngineSelect`, delante de la acción como en las cabeceras de los
dos tableros, criterio C-2); el botón dice cuántas van. Elegir motor por
partida convertiría un botón en un formulario, y la pregunta de quien analiza
en lote es con cuál quiere esta remesa; para el caso de una sola ya están el
visor y el tablero de análisis. La casilla de la cabecera marca **solo la
página visible** —una tanda de trescientas partidas que no se han visto se
pide a ciegas— y lo marcado se vacía al cambiar de filtro, al pasar de página
(`goToPageAtOffset`) y al mandar la tanda, para que el botón nunca cuente
partidas que no están en pantalla. Todo eso se explica en la frase bajo la
barra y no en un `title`, que con teclado no aparece (criterio C-3). El
`SuccessBox` nombra el motor con el que se mandaron leyéndolo de la respuesta y
no del desplegable, que se puede cambiar mientras el recuadro sigue ahí. Las
partidas se analizan en segundo plano (RF-2.4): la petición es un solo `POST
/analysis` con la lista de ids.

**La columna «Análisis»** dice con qué motores está analizada cada partida, que
es lo que permite componer la tanda sin adivinar. No es un sí o un no: una
partida puede estar analizada con Stockfish y con Lc0 (RF-2.6). Sale de
`analyzed_by_engines` y `has_analysis_in_progress` de `GET /games`, que la API
saca de la tabla `analyses` y no de `games`, y la compone
`formatAnalyzedByEngines` de `lib/format.ts`. Dos cosas que quedan pendientes y
están en el inventario de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md): la
columna no se refresca sola mientras hay análisis en marcha (fila 110) y la
tanda no avisa de lo que va a reanalizar (fila 111).

Una partida importada llega con huecos donde el PGN no decía nada —los dos
ratings, el control de tiempo y el ritmo—, y la tabla los enseña como "—" con
`formatRating`, `formatTimeControl` y `formatTimeClass` de `lib/format.ts`, el
mismo hueco que la precisión sin analizar (criterio C-5). **"Sin analizar" de
la columna «Análisis» no es ese hueco**: el guion dice que un dato no llegó, y
ahí no falta nada —se sabe que nadie mandó analizar esa partida—, así que se
dice con las mismas palabras que ya usan los `EmptyState` del visor y del
tablero de análisis (`NOT_ANALYZED`, criterios C-5 y C-6).

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

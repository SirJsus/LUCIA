# ADR-0012 · El deshacer del tablero de análisis es un historial lineal guardado en la base

**Estado:** aceptado · **Fecha:** 2026-09-18

## Contexto

RF-6.8 pide "autoguardado y control de versiones simple (deshacer/rehacer
sobre el árbol)". El autoguardado ya estaba desde el núcleo de RF-6: el
tablero escribe `boards.tree_json` con un pequeño retardo cada vez que el
árbol cambia. Lo que faltaba es poder retirar lo último hecho.

El material con el que se trabaja no es texto sino un árbol de variantes
(`tree.ts`), que vive entero como JSON opaco en una columna
([03-arquitectura.md § modelo de datos](../03-arquitectura.md)). Un tablero
trabajado pesa unos pocos kilobytes.

Las opciones eran tres:

1. **Pila en memoria del navegador**: guardar los árboles anteriores en un
   `useRef` de `BoardPage` y no tocar la base.
2. **Historial lineal persistido**: una tabla de versiones y un puntero en
   `boards` a la que se está viendo.
3. **Árbol de versiones persistido** (estilo `git`): deshacer crea una rama y
   nada se descarta nunca.

## Decisión

**La opción 2.** Tabla `board_versions` (`board_id`, `root_fen`, `tree_json`,
`created_at`) con el árbol **entero** en cada fila, y `boards
.current_version_id` como **cursor**: no es "la última versión" sino "la que
se está viendo". Deshacer mueve el cursor hacia atrás sin borrar nada;
rehacer, hacia delante; y la primera edición después de deshacer descarta lo
que quedaba por delante, como en un editor de texto.

Va con ella:

- **Solo lo que cambia el árbol anota versión.** `record_version` se llama
  desde `PUT /boards/{id}` cuando llega `tree_json` o `root_fen`, no cuando
  se renombra el tablero o se marca como partida propia.
- **Se guarda el `root_fen` con cada versión**, no solo el árbol: importar un
  PGN puede mover la posición de partida (RF-6.7).
- **Tope de 50 versiones por tablero** (`MAX_VERSIONS_PER_BOARD`), podando
  siempre por el extremo antiguo.
- **El orden del historial es por `id`**, no por `created_at`.
- **`can_undo`/`can_redo` viajan en `BoardDetail`**: el front no sabe cuántas
  versiones hay.

## Razones

- **El deshacer tiene que sobrevivir a recargar.** El tablero ya se guarda
  solo; con la opción 1, cerrar la pestaña por accidente y volver dejaba el
  árbol correcto y el historial vacío, así que lo último autoguardado —que
  puede ser justo el error— quedaba fijo para siempre. Un deshacer que
  desaparece sin avisar es peor que no tenerlo, porque nadie lo espera.
- **Lineal porque la pantalla ya tiene un árbol.** La opción 3 es más potente
  y no pierde nada, pero obliga a explicar en la interfaz dos estructuras de
  árbol a la vez —las variantes de la partida y las versiones del documento—
  y a que el usuario distinga entre ellas. Quien pulsa Ctrl+Z quiere retirar
  la jugada que acaba de poner, no navegar un historial.
- **El árbol entero y no un diff.** Un tablero pesa kilobytes: con el tope de
  50 versiones, lo peor que puede pasar son unos cientos de kB por tablero en
  una base local (ADR-0005). Reconstruir un estado aplicando diferencias es
  código que solo falla cuando hace falta, y aquí el dato que se perdería es
  precisamente el que el usuario quería recuperar.
- **El cursor en vez de borrar al deshacer.** Si deshacer borrara la versión,
  rehacer necesitaría otra pila que guardar en algún sitio; con el cursor,
  las dos direcciones son la misma consulta con el signo cambiado
  (`_adjacent_version`).
- **Por `id` y no por fecha**, por lo mismo que en `latest_analysis_ids`: el
  id es monótono y no empata, mientras que dos versiones guardadas en el
  mismo segundo tienen la misma fecha y deshacer se quedaría dando vueltas
  entre ellas.
- **El tope existe para que esto no sea un control de versiones.** Es "deshaz
  lo que acabas de hacer". Sin tope, un tablero muy trabajado acumularía
  miles de copias de sí mismo que nadie va a mirar.

## Consecuencias

- **Deshacer cuesta una petición**, no es instantáneo como una pila local.
  A cambio, el estado que se ve tras deshacer es exactamente el que está
  guardado: no hay forma de que la pantalla y la base discrepen.
- **Hay que vaciar el autoguardado pendiente antes de deshacer**
  (`flushPendingSave` en `BoardPage`). El autoguardado escribe con retardo;
  sin esto, deshacer justo después de mover retiraría la jugada anterior y la
  recién hecha se escribiría encima al vencer la espera. Cualquier acción
  nueva que lea del servidor lo que hay en pantalla tiene la misma obligación
  — analizar el tablero (RF-6.9) ya la cumple.
- **Se pierde lo más antiguo sin avisar** al pasar de 50 versiones. Es
  deliberado, pero significa que esto no sirve para recuperar un tablero como
  estaba la semana pasada.
- **`boards.current_version_id` no tiene `ForeignKey`.** Declarar las dos
  direcciones (tablero → versión y versión → tablero) deja un ciclo de tablas
  que SQLite no puede romper, porque no sabe añadir una restricción después
  de crear la tabla. Las versiones se borran en cascada con su tablero, así
  que el puntero no queda colgando; la integridad la sostiene esa cascada, no
  el esquema.
- **Puesto al día por [ADR-0014](0014-tablero-propio-publicado-como-partida.md)
  el mismo día**, en dos cosas que esta decisión da por hechas: cada versión
  guarda además su PGN (`board_versions.pgn`, migración `d4b7e0c25a19`), para
  que deshacer arrastre consigo la partida de un tablero publicado como
  propia; y la cascada que aquí sostiene el puntero sin `ForeignKey` **no se
  ejecutaba**, porque sqlite traía las claves foráneas apagadas por conexión
  hasta que `db/base.py::create_db_engine` empezó a encender
  `PRAGMA foreign_keys=ON`.
- **Qué NO fija.** Ni cuántos pasos se enseñan en la interfaz (hoy, botón
  activo o inactivo) ni que el historial siga siendo lineal si algún día se
  quiere versionar un tablero de verdad: eso sería otra decisión, con su ADR,
  y probablemente otra tabla.

## Ver también

- RF-6.8 en [02-requerimientos.md](../02-requerimientos.md), con la nota de
  cómo se cumplió.
- [03-arquitectura.md](../03-arquitectura.md): flujo 9 y el modelo de datos.
- `apps/api/lucia_api/services/boards.py`,
  `apps/api/lucia_api/routers/boards.py` (`/undo`, `/redo`) y
  `apps/web/src/features/board/useUndoRedoKeys.ts`.
- Migración `97d2b0821d2b`.

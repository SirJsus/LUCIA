# ADR-0011 · Las partidas importadas de un PGN viven en `games` como las de chess.com

**Estado:** aceptado · **Fecha:** 2026-09-17

## Contexto

RF-1.5 pide traer al historial partidas de otras fuentes: un archivo de
torneo, una partida sobre el tablero, una exportación de lichess. Hasta ahora
todo lo que hay en `games` viene del sincronizador de chess.com
([03-arquitectura.md § Flujos](../03-arquitectura.md)), que trae siempre las
mismas columnas llenas: identificador propio (`uuid`), rating de los dos
bandos, control de tiempo y categoría de ritmo, si la partida era puntuada y
cómo acabó exactamente ("agreed", "stalemate", "repetition"…).

Un PGN manual no trae casi nada de eso. Trae las jugadas, los nombres de los
dos jugadores tal como los escribiera quien generó el archivo, a veces la
fecha, y un resultado de tres valores ("1-0", "0-1", "1/2-1/2", más "\*" para
las que no terminaron). Los nombres, además, no son usuarios: un PGN de
torneo dice "Durán, Jesús", y el dashboard (RF-3) y los filtros por color,
resultado y rival (RF-5.3) casan por `username`.

Las opciones eran tres:

1. **Tabla aparte** para las partidas manuales, con sus propias columnas
   (solo las que un PGN puede llenar) y sus propias consultas.
2. **Misma tabla, columnas opcionales**: hacer `NULL`-ables `white_rating`,
   `time_class`, `time_control` y `rated`.
3. **Misma tabla, con huecos explícitos**: mismas columnas obligatorias,
   rellenas con valores que se reconocen como "no se sabe".

## Decisión

**La opción 3.** Una partida importada de un PGN es una fila normal de
`games`, con `platform = "manual"`, y lo que el archivo no dice se guarda
como hueco: rating `0`, `time_class` `"unknown"`, `time_control` `"-"`,
`rated` `false`. El resultado de tablas se guarda como `"draw"` a secas, un
valor más del vocabulario de `DRAW_RESULTS`. Las partidas sin terminar ("\*")
y las que no traen jugadas no se importan, y la respuesta dice cuáles y por
qué.

Dos decisiones que van con ella:

- **La identidad de una partida manual es el SHA-256 de su PGN**, guardado en
  `platform_id`. No hay identificador de origen que usar.
- **La atribución es por nombre, y la declara el usuario**: el formulario
  pregunta cómo aparece él dentro de ese archivo (`player_name_in_pgn`) y ese
  bando se guarda con su `username` de LUCIA. El jugador al que cuelgan las
  partidas se busca por `username` en cualquier plataforma, no solo en
  "manual", para caer en la misma fila que creó la sincronización.

## Razones

- **El resto de la aplicación no debería enterarse.** El visor, el análisis,
  las estadísticas, los filtros y el repertorio consultan `games`. Con la
  opción 1, cada uno de ellos tendría que unir dos tablas o elegir una, y la
  pregunta "¿cuántas partidas he jugado?" tendría dos respuestas distintas
  según quién la haga. El coste de la opción 3 es local —cuatro valores que
  significan "no se sabe"—; el de la 1 se paga en cada consulta futura.
- **Hacer las columnas opcionales cambiaría el significado de lo ya guardado.**
  Con la opción 2, un `time_class` `NULL` obligaría a revisar todas las
  consultas existentes, que hoy dan por hecho que hay ritmo, y no ganaría
  nada: un hueco declarado se reconoce igual de bien y no toca la migración.
  El precio es que el hueco hay que conocerlo para leerlo, y por eso vive en
  una constante con nombre en los dos lados (`lib/format.ts` en el front,
  el importador en la API) y se enseña siempre como "—" (criterio C-5 de
  [07-coherencia-ui.md](../07-coherencia-ui.md)).
- **No inventar el dato que falta.** Un "40/7200:1800" de torneo no es
  bullet, ni blitz, ni rapid, ni daily: traducirlo a una de esas categorías
  metería partidas de cinco horas en el marcador de "rapid" y las
  estadísticas mentirían sin avisar. Un rating "estimado" sería peor todavía.
  Enseñar "—" es exacto.
- **El hash del PGN hace la importación idempotente**, que es la propiedad
  que ya tiene el sincronizador por `uuid`: volver a subir el archivo del
  torneo, con dos partidas más al final, reescribe las viejas y añade las
  nuevas. La contrapartida está en Consecuencias.
- **El nombre lo pone el usuario porque nadie más puede.** Adivinarlo
  —comparando el `username` con los dos bandos, o quedándose con el jugador
  que más se repite en el archivo— acierta a veces y falla en silencio: la
  partida se guardaría igual y no contaría en ningún marcador. Preguntarlo es
  un campo más en el formulario y una respuesta que dice en cuántas partidas
  se reconoció al usuario (`games_matched_to_player`), de modo que el fallo se
  ve al importar y no semanas después.

## Consecuencias

- **Editar el PGN crea una partida nueva.** Corregir un nombre mal escrito o
  añadir una cabecera cambia el hash, así que reimportar el archivo corregido
  deja las dos versiones. Es el precio de no tener identificador de origen;
  el remedio, mientras no haya pantalla para borrar partidas, es borrar la
  fila vieja a mano.
- **Una partida manual no aparece en las estadísticas por ritmo ni por
  rating.** No es un defecto de la agregación: no hay dato que agregar. Las
  que sí la incluyen —marcador, aperturas, errores por tipo, precisión— son
  las que dependen de las jugadas, que es lo que el PGN sí trae.
- **La atribución mal escrita se puede arreglar reimportando** con el nombre
  correcto: el hash no cambia, así que la fila se reescribe en vez de
  duplicarse. Por eso importa que el aviso se vea en el momento.
- **`platform` deja de significar "de dónde se descargó"** para significar
  "de dónde vino": `"manual"` no es un sitio al que se pueda volver a
  preguntar. Cualquier código que asuma que una partida se puede re-descargar
  de su plataforma tiene que mirar ese campo.
- **Qué NO fija.** Ni el formato del archivo (cualquier cosa que
  `python-chess` sepa leer entra igual) ni el tope de 5 MB de la subida, que
  es una defensa del router y no una decisión de arquitectura. Tampoco
  descarta que en el futuro una partida manual reciba rating o ritmo a mano:
  eso sería llenar el hueco, no cambiar la decisión.

## Ver también

- RF-1.5 en [02-requerimientos.md](../02-requerimientos.md), con la nota de
  cómo se cumplió.
- [03-arquitectura.md](../03-arquitectura.md): el flujo de importación y el
  modelo de datos.
- `apps/api/lucia_api/services/pgn_import.py` (el importador) y
  `apps/api/lucia_api/routers/pgn_import.py` (`POST /import/pgn`).

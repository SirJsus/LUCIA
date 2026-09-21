# ADR-0019 · El drill de aperturas se construye sobre las salidas de la teoría y "peor" se mide en puntos perdidos

**Estado:** aceptado · **Fecha:** 2026-09-21

## Contexto

RF-4.2 pide "repetir las líneas donde mi rendimiento es peor". La frase deja
tres huecos, y los tres hay que rellenarlos antes de escribir una línea de
código: **qué es una línea**, **de dónde sale** y **qué es peor**.

Lo que ya había en LUCIA para responder:

- **Las salidas de la teoría de RF-3.6**: los puntos donde se abandona el
  libro de maestros, agrupados por color, momento y jugada, con el marcador de
  todas las partidas que se salen por ahí y con lo que los maestros juegan en
  esa posición. Es el único sitio del proyecto donde hay una **respuesta
  afirmable** para una decisión de apertura.
- **Las aperturas de RF-3.2**: cuántas partidas y qué marcador por apertura y
  color, con la clasificación ECO propia. Dice dónde va mal, pero no qué
  jugada arreglarlo.
- **La caché del Opening Explorer** (`explorer_positions`), que se llena
  **solo cuando se pide** y con tope por llamada
  ([ADR-0010](0010-repertorio-con-red-y-cacheado.md)), porque RNF-1 dice que
  la aplicación funciona sin red.

Las opciones eran:

1. **Drill = posición suelta**, como un puzzle de RF-4.1 pero en la apertura:
   la posición anterior a la salida y la jugada de maestros como respuesta.
2. **Drill = línea principal de la apertura mala**, descargada del explorador:
   tomar las aperturas con peor marcador de RF-3.2 y bajar su línea teórica
   siguiendo la jugada más jugada por los maestros durante N jugadas.
3. **Drill = el camino propio de una partida, corregido en la salida**: las
   jugadas tal como se jugaron hasta el punto donde se abandonó el libro, más
   la jugada de maestros que había que hacer ahí; elegido por dos criterios
   distintos —la salida en sí (RF-3.6) o la apertura a la que lleva
   (RF-3.2)— sobre ese mismo material.

Y, en paralelo, qué es "peor": un **corte por porcentaje** ("por debajo del
45 %") o una medida de **daño acumulado**.

## Decisión

**La opción 3, y "peor" medido en puntos perdidos.**

- **La línea es el camino propio corregido**: `line_uci_from_departure` toma
  las jugadas de los dos bandos hasta el ply de la salida y le añade la jugada
  **más jugada por los maestros** en esa posición. Termina ahí: no continúa
  por la línea principal.
- **Las dos barajas comparten material.** "Salidas de la teoría"
  (`reason="departure"`, RF-3.6) y "peores aperturas" (`reason="opening"`,
  RF-3.2) se construyen exactamente igual y se recorren en el mismo bucle; lo
  único que cambia es **por qué entra** una línea y qué partidas y qué marcador
  la justifican. `reason` es lo único que las distingue después.
- **"Peor" es daño, no porcentaje**: `points_lost(games, score_percent) =
  games * (50 - score_percent) / 100`. Entra lo que cueste puntos —umbral
  cero— y se juega antes lo que cueste más. El único umbral duro es de hábito:
  `MIN_GAMES_TO_DRILL` = 3 partidas.
- **Una salida sin jugada de maestros no genera drill**, y una apertura mala
  en la que nunca se abandona el libro tampoco.
- **Tabla propia `opening_drills`**, con la línea y el motivo congelados al
  generar, sin clave foránea a la partida de la que salió, con su estado de
  SM-2 y clave única `(player_color, line_uci)`.
- **El servidor es el árbitro y el rival, y no guarda progreso.** La línea no
  viaja mientras el drill está abierto; el servidor comprueba cada jugada,
  contesta por el rival y solo al cerrar manda la línea entera. Por dónde va
  el drill lo lleva la pantalla.

## Razones

- **La opción 1 no entrena lo que se olvida.** Lo que falla en una apertura no
  es reconocer una posición, es el camino: se llega a la jugada 6 por inercia
  y se hace la de siempre. Plantar al usuario en la posición anterior a la
  salida le regala justo la parte que no recuerda —cómo se llegó ahí— y
  convierte un problema de repertorio en un problema de "encuentra la jugada",
  que ya es RF-4.1.
- **La opción 2 pide una red que RF-3.6 no ha pedido.** Bajar la línea
  principal de una apertura son N consultas nuevas al explorador por cada
  drill, sobre posiciones que la comparación de repertorio nunca visita. Eso
  rompe el trato de [ADR-0010](0010-repertorio-con-red-y-cacheado.md): la
  caché se llena cuando el usuario lo pide y con tope, no cuando una pantalla
  de entrenamiento lo necesita. Además el drill saldría de un libro y no de
  las partidas propias, que es lo que RF-4.2 dice ("**mi** rendimiento").
- **Que las dos barajas compartan material es lo que hace afirmable la
  segunda.** RF-3.2 sabe que una apertura va mal, pero no qué hacer al
  respecto; sin una salida de la teoría dentro de ella no hay ninguna jugada
  que se pueda enseñar como "la que había que hacer". Por eso una apertura
  mala sin salidas **no da drill**: no es un hueco de cobertura, es la
  respuesta honesta —ahí el problema no es la apertura, es lo que viene
  después, y eso son los puzzles de RF-4.1.
- **El porcentaje suelto ordena mal.** Tres partidas al 20 % cuestan nueve
  décimas de punto; quince al 40 % cuestan punto y medio. Un corte absoluto
  deja fuera la segunda, que es el agujero grande: sangra despacio y muchas
  veces, y es justo el que un repertorio debería tapar primero. Medido sobre
  las 326 partidas reales del autor, el corte por porcentaje daba 3 líneas y
  ordenar por daño da 10, encabezadas por las que de verdad cuestan puntos.
  Por eso el umbral que queda es cero: poner uno más alto sería decidir por
  quien entrena dónde está su problema, y para eso ya está el orden.
- **La línea congelada, por lo mismo que el puzzle**
  ([ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md)): un drill
  lleva encima un historial de repasos que no está en ninguna otra parte, y
  volver a sincronizar, reanalizar o refrescar el repertorio no puede
  llevárselo por delante. El motivo (`games`, `score_percent`) se congela con
  ella: cambiarlo bajo un historial ya hecho falsearía ese historial.
- **La clave única es `(bando, línea)` y no la partida de origen**, al revés
  que en los puzzles (`(game_id, ply)`). Un drill no es de una partida: la
  gracia es que la misma línea se repite en muchas, y el camino hasta la
  salida es el mismo por construcción —las salidas se agrupan por color,
  momento y jugada, así que la posición es idéntica. Con la partida en la
  clave, la misma línea entraría una vez por partida.
- **El servidor no guarda progreso porque no hay progreso que guardar.** Un
  drill se repite entero o no se repite: retomarlo por la jugada 5 no entrena
  el camino, que es lo único que entrena. El `ply` vive en la pantalla igual
  que el número de intento de un puzzle.
- **La línea no puede viajar**, y aquí con más razón que en los puzzles: el
  navegador no solo sabría la respuesta, sabría también qué va a contestar el
  rival. Que el servidor responda jugada a jugada es lo que permite jugar la
  línea sin conocerla.

## Consecuencias

- **El drill hereda la cobertura de RF-3.6, para bien y para mal.** Solo hay
  drills donde hay teoría consultada; mientras `positions_missing` no sea
  cero, la baraja crece cada vez que se refresca el repertorio, y la pantalla
  lo dice en vez de dejar creer que no hay material. Sobre las 326 partidas
  del autor, con 150 posiciones traídas, salían 49 salidas —la mayoría en los
  plies 2-3—, 10 drills y 42 posiciones por consultar.
- **Las líneas son cortas**, porque las salidas son tempranas. Un drill de dos
  o tres jugadas propias es lo normal, y es coherente: si la teoría se abandona
  en el ply 3, repetir hasta el 12 sería entrenar una línea que nunca se ha
  jugado.
- **La línea no continúa más allá de la salida**, y es una limitación
  conocida: se termina en la jugada buena, no se recorre la teoría que sigue.
  Alargarla exigiría consultar posiciones nuevas al explorador, que es
  exactamente lo que se descartó en la opción 2; el día que se quiera, el
  cambio es traerlas al refrescar el repertorio (RF-3.6) y no al generar
  drills.
- **Esto no añade un algoritmo de repaso.** Un drill se reparte y vuelve con
  el mismo SM-2 de `lucia_core.training` que los puzzles, con la misma cola y
  las mismas tres notas. `lucia_core.training` deja de ser "las reglas de los
  puzzles" para ser "las reglas del repaso", y tiene ahora dos servicios que
  lo usan.
- **`Departure` (RF-3.6) creció dos campos** —`master_moves_uci` y
  `preceding_moves_uci`— que la comparación de repertorio no mira. Están ahí
  porque el camino y la jugada en UCI solo se pueden componer mientras se
  recorre la partida, y volver a recorrerla desde el drill sería hacer dos
  veces el mismo trabajo con el riesgo de que las dos pantallas no coincidan.
- **Qué NO fija este ADR.** Cuántas partidas hacen falta
  (`MIN_GAMES_TO_DRILL`), cuántas aperturas se miran
  (`MAX_OPENINGS_CONSIDERED`), cuántos drills se reparten de una vez o cuántas
  jugadas de maestros se guardan por posición son constantes con nombre,
  revisables sin tocar nada más. Cambiar el criterio de "peor" a un corte por
  porcentaje, mandar la línea al navegador o generar drills bajando teoría
  nueva del explorador, en cambio, sí sería cambiar esta decisión.

## Ver también

- RF-4.2 en [02-requerimientos.md](../02-requerimientos.md), con las reglas
  concretas con las que se cumplió, y las notas de RF-3.6 y RF-3.2, que son el
  material del que sale.
- [ADR-0010](0010-repertorio-con-red-y-cacheado.md): por qué la teoría se trae
  solo cuando el usuario lo pide, que es lo que acota el alcance del drill.
- [ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md): la misma
  decisión de congelar el material de entrenamiento y desacoplarlo de su
  origen, aquí aplicada a una línea en vez de a una posición.
- [ADR-0018](0018-sparring-en-su-propia-tabla-y-el-servidor-como-arbitro.md):
  el servidor como árbitro, que aquí se repite — aunque un drill no es una
  partida y por eso no guarda estado entre peticiones.
- `packages/core/lucia_core/drills/__init__.py` (las reglas puras),
  `apps/api/lucia_api/services/drills.py` (de dónde sale el material),
  `apps/api/lucia_api/routers/drills.py` (qué se manda y qué no) y la tabla
  `opening_drills` en [03-arquitectura.md](../03-arquitectura.md).

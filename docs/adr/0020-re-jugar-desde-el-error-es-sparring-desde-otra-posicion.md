# ADR-0020 · "Re-juega desde el error" es sparring desde otra posición, y la lista de errores no se persiste

**Estado:** aceptado · **Fecha:** 2026-09-21

## Contexto

RF-4.4 pide "retomar una partida propia desde la posición del blunder contra el
motor". Cuando llega, casi todo lo que necesita ya existe:

- **Jugar contra el motor** está resuelto desde RF-4.3
  ([ADR-0018](0018-sparring-en-su-propia-tabla-y-el-servidor-como-arbitro.md)):
  `sparring_games`, `EngineBridge.play`, el servidor como árbitro y
  `starting_fen` ya en columna precisamente para esto.
- **Saber qué errores tiene el jugador** está resuelto desde RF-4.1: los
  `analyzed_moves` clasificados como `mistake`, `blunder` o `missed_win` son
  los mismos que dan puzzle (`PUZZLE_CLASSIFICATIONS`).

Lo que no estaba decidido era cómo se juntan, y la forma de juntarlos tiene
tres preguntas con respuesta no obvia:

1. **¿Una partida retomada es una partida de sparring o es otra cosa?** De
   ella se puede decir que empieza a mitad, que tiene una partida detrás y que
   se abre desde otra pantalla; eso invitaba a una tabla propia,
   `replay_games`, con su enlace a la jugada de origen.
2. **¿La lista de "errores desde los que re-jugar" se guarda?** Es la misma
   pregunta que ya se hizo dos veces en el proyecto con dos respuestas
   contrarias: los patrones se deducen al leer
   ([ADR-0008](0008-patrones-deducidos-al-leer.md)) y los puzzles se persisten
   con su solución congelada
   ([ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md)).
3. **¿Desde dónde se puede retomar, y quién decide la posición?** El texto del
   requerimiento dice "la posición del blunder", en singular. Y justo al lado
   hay un requerimiento congelado fuera de v1.0, **RF-11.1**, que pide jugar
   contra el motor "desde una posición inicial personalizada —la del editor de
   RF-6.1 o un FEN— eligiendo color y bando con ventaja". Una implementación
   generosa de RF-4.4 puede acabar siendo RF-11.1 por la puerta de atrás, y
   entonces el corte de alcance de v1.0 deja de ser verdad.

## Decisión

**Retomar es abrir una partida de sparring desde otra posición, la lista no se
guarda, y la posición siempre la deriva el servidor de un PGN que ya tiene.**

- **Misma tabla, mismo ciclo, misma pantalla.** No hay `replay_games`:
  `sparring_games` gana dos columnas, `origin_game_id` y `origin_ply`
  (migración `d5a81c6e3f04`). Se juega en `SparringGamePage` y se lista en
  `SparringPage` junto a las demás, con una insignia "re-jugada".
- **`origin_*` es procedencia, no dependencia.** `ON DELETE SET NULL` y sin
  cascada: borrar la partida de origen no invalida lo jugado, solo deja de
  haber adónde volver. La posición está en `starting_fen`, que es lo que hace
  la partida jugable.
- **La lista de errores se deduce al leer.** `GET /training/replays`
  (`services/replays.py`) recorre los análisis terminados más recientes cada
  vez que se pregunta. No hay tabla, no hay generación, no hay botón de
  generar.
- **La posición la deriva el servidor** (`lucia_core.sparring.board_at_ply`
  sobre `games.pgn`). Por HTTP se manda **de qué partida y de qué jugada**
  (`SparringOriginIn: {game_id, ply}`), nunca un FEN.
- **Se puede retomar cualquier posición de la partida y con cualquier bando**,
  desde el visor ("Jugar desde aquí"). La lista curada de la pestaña
  "Re-jugar" se ciñe a los errores graves, los mismos de
  `PUZZLE_CLASSIFICATIONS`, ordenados por lo que costaron.
- **Quién abre no es "las blancas"** sino quien tenga el turno en la posición
  de partida.
- **Lo que costó el error viaja en la lista.** `win_percent_before` y
  `win_percent_after` van en `ReplayPositionOut` sin esconderse, al revés que
  en un puzzle abierto.

## Razones

- **Una partida retomada no se comporta distinto de una de sparring.** Se
  mueve igual, el servidor arbitra igual, termina igual, se analiza igual
  (abrirla como tablero, RF-6.6, y analizar desde ahí, RF-6.9) y no cuenta en
  estadísticas por el mismo motivo. Lo único que cambia es en qué posición
  empieza — y eso ya era una columna. Una tabla aparte habría duplicado el
  router, el servicio, la pantalla de juego y las reglas de final por una
  diferencia que cabe en dos enteros nulos.
- **La lista no lleva encima ningún estado propio**, y ahí está la línea que
  separa esta decisión de la de los puzzles. Un puzzle se persiste porque
  arrastra un historial de repasos SM-2 que no está en ninguna otra parte, y
  su solución se congela porque re-analizar la partida no debe cambiar la
  respuesta de un ejercicio ya repasado (ADR-0017). Una posición desde la que
  re-jugar no se repasa, no vence, no acumula intentos: es una **vista** de
  `analyzed_moves`. Guardarla solo daría una segunda copia que envejece en
  cuanto se reanaliza la partida con otro motor o a otra profundidad, que es
  exactamente el argumento de ADR-0008 para los patrones. La regla que queda
  escrita, y que sirve para la siguiente vez que se plantee: **se persiste lo
  que lleva estado propio; lo que solo es una lectura de lo que ya hay, se
  deduce al leer.**
- **No aceptar un FEN por HTTP es lo que mantiene la frontera con RF-11.1.**
  Si `POST /sparring/games` aceptara una posición cualquiera, el editor de
  posición de RF-6.1 tendría un botón "jugar esto" a un `fetch` de distancia y
  RF-11.1 estaría medio implementado sin haberse movido al alcance de v1.0.
  Pidiendo `{game_id, ply}` la API no sabe empezar una partida desde una
  posición que no haya jugado ya el usuario.
- **Dejar retomar cualquier posición es una lectura generosa del texto, y
  aun así no invade RF-11.1.** "Desde la posición del blunder" es un ejemplo
  del caso que importa, no una restricción: la jugada anterior al error suele
  ser donde ya se estaba peor, y una apertura que va mal se rehace desde la
  jugada 6 y no desde la 24. Lo que separa esto de RF-11.1 no es cuántas
  posiciones se ofrecen, son tres cosas: **(a)** las posiciones salen de
  partidas propias ya guardadas, no de un FEN pegado ni del editor; **(b)** no
  hay ninguna perilla de ventaja material, que es el corazón de RF-11 —la
  segunda perilla de dificultad de RF-11.2—; y **(c)** no se guarda como
  partida con `[SetUp "1"]` en `games`, que es lo que pide RF-11.3. RF-11.1
  sigue entero fuera de v1.0.
- **Elegir bando también es de RF-4.4 y no de RF-11.1.** Rehacer un error
  jugándolo desde el otro lado es entrenar la posición, no darse ventaja; y la
  alternativa —fijar el bando— obligaría además a explicar por qué desde el
  visor no se puede pedir la posición del rival, que es una pregunta sin buena
  respuesta.
- **El turno lo manda la posición, no el color.** Dando por hecho que "abre
  quien lleva blancas" —que es lo que valía mientras toda partida empezaba en
  la posición inicial— una partida retomada en una posición con las negras al
  turno se quedaba esperando a nadie. `create_game` compara el turno de la
  posición con el bando elegido.
- **Enseñar lo que costó el error no contradice que un puzzle lo esconda.** En
  un puzzle abierto la evaluación es media respuesta: se viene a encontrar la
  jugada. Aquí no hay nada que adivinar —la jugada que se hizo está en la
  lista, en rojo, y de lo que se trata es de jugar la posición mejor de lo que
  se jugó—, y cuánto costó es justo el dato que responde "¿por cuál empiezo?".
  Es el mismo criterio de ADR-0017 aplicado, no invertido: no se enseña lo que
  resuelve el ejercicio, y aquí el ejercicio es la partida entera.

## Consecuencias

- **`sparring_games` deja de ser una tabla de partidas anónimas.** Tiene una
  clave foránea a `games`, y con ella la primera relación entre el
  entrenamiento y el historial que no pasa por copiar el dato. Es lo contrario
  de lo que hacen `puzzles` y `opening_drills`, que se guardan desenganchados
  de la partida de la que salieron (ADR-0017): allí la copia protege un
  historial de repasos, aquí el enlace solo sirve para poder volver.
- **`starting_fen` ya no es siempre la posición inicial**, así que todo lo que
  numera jugadas de una partida de sparring pasa a ser relativo a ella.
  `to_pgn` ya escribía `[SetUp "1"]` + `[FEN ...]` cuando hacía falta; lo que
  queda desalineado es la numeración de la lista de jugadas en pantalla, que
  empieza en 1 aunque la partida empiece en la jugada 24 — apuntado como fila
  abierta en [07-coherencia-ui.md](../07-coherencia-ui.md) porque arreglarlo
  pide que el ply de salida viaje en `SparringGameOut`.
  **Actualización 2026-09-22**: cerrado con `starting_ply` —derivado de
  `starting_fen` y no de `origin_ply`—, que numera tanto la lista de jugadas
  como la frase «Retomada desde la jugada 23»; ver la fila **101**, ya cerrada,
  del inventario de [07-coherencia-ui.md](../07-coherencia-ui.md).
- **Hay dos puertas a lo mismo, y es a propósito.** La pestaña "Re-jugar"
  responde "¿por dónde empiezo?" con la lista curada; el visor responde
  "quiero rehacer *esta*" desde cualquier posición. Las dos usan el mismo
  `SparringSetupForm` y el mismo endpoint, así que no hay dos formas de elegir
  dificultad que mantener.
- **`GET /training/replays` no tiene caché ni paginación.** Es una consulta
  agregada sobre `analyzed_moves` con `LIMIT`
  (`DEFAULT_POSITIONS_LIMIT` = 20): una lista para elegir, no un inventario.
  Si algún día hiciera falta paginarla, no rompe nada guardado, que es
  justamente la ventaja de no persistirla.
- **Qué NO fija este ADR.** Cuántas posiciones se ofrecen, qué
  clasificaciones entran en la lista curada y cómo se ordenan son constantes
  con nombre, revisables sin tocar nada más. Aceptar un FEN por HTTP, guardar
  la lista de errores o añadir una perilla de ventaja material sí sería
  cambiar esta decisión — y lo tercero, además, meter RF-11 dentro de v1.0.

## Ver también

- RF-4.4 en [02-requerimientos.md](../02-requerimientos.md), con las reglas
  concretas con las que se cumplió, y la nota técnica de RF-11, que dice qué le
  sigue faltando de verdad a RF-11.1 después de esto.
- [ADR-0018](0018-sparring-en-su-propia-tabla-y-el-servidor-como-arbitro.md):
  la partida de sparring, sobre la que esto se construye entero.
- [ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md) y
  [ADR-0008](0008-patrones-deducidos-al-leer.md): las dos respuestas contrarias
  a "¿esto se guarda?", y el criterio que las separa.
- `packages/core/lucia_core/sparring/__init__.py` (`board_at_ply`),
  `apps/api/lucia_api/services/replays.py` y `routers/replays.py` (la lista),
  `apps/api/lucia_api/services/sparring.py` (`get_sparring_origin`, `create_game`
  con `origin`), `apps/web/src/features/training/ReplaysPage.tsx` y
  `SparringSetupForm.tsx`, y la tabla `sparring_games` en
  [03-arquitectura.md](../03-arquitectura.md).

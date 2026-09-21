# ADR-0018 · La partida de sparring vive en su propia tabla, se guarda como jugadas y el servidor es el rival y el árbitro

**Estado:** aceptado · **Fecha:** 2026-09-21

## Contexto

RF-4.3 pide jugar contra el motor con la fuerza calibrada: Stockfish
conteniéndose con `UCI_LimitStrength`/`UCI_Elo`, o Lc0 con una red tipo Maia
para que el rival juegue como una persona. Es la primera vez en LUCIA que el
motor **mueve** en vez de opinar: hasta aquí `EngineBridge` solo analizaba, y
la nota técnica de RF-11 lo señalaba como la carencia que compartían RF-4.3,
RF-4.4 y RF-11.

Una partida así se parece a dos cosas que ya existen, y a ninguna del todo:

- **A una partida de `games`** (RF-1), porque tiene dos bandos, jugadas,
  resultado y PGN. Pero no es historial: es contra un motor al que se le ha
  bajado la fuerza, y contarla en estadísticas o en detección de patrones
  (RF-3) sería medir el rendimiento real con partidas que no lo son. RF-6.5
  ya había puesto esa frontera para los tableros de análisis y RF-11.3 la
  repite palabra por palabra para las partidas con ventaja.
- **A un tablero de análisis** (RF-6), porque es una posición que evoluciona y
  que se guarda entre visitas. Pero en un tablero la API custodia un documento
  opaco y quien sabe de reglas es chess.js en el navegador
  ([ADR-0013](0013-analisis-de-partida-o-de-tablero.md) y el `tree_json` que
  la API no interpreta). En sparring el servidor no puede ser un archivador:
  tiene que contestar a la jugada.

Las opciones eran:

1. **Guardarla como una fila de `games`**, con una marca que la excluyera de
   las estadísticas, igual que se pensó en su día para los tableros.
2. **Guardarla como un tablero** (`boards`), reutilizando el árbol, el
   historial y el análisis que ya cuelgan de ahí.
3. **Tabla propia `sparring_games`**, con lo mínimo de lo que todo lo demás se
   deriva, y el camino ya existente (abrir como tablero, RF-6.6, y analizar
   desde ahí, RF-6.9) para cuando se quiera estudiar la partida.

## Decisión

**La opción 3, y con el servidor como autoridad de reglas dentro de ella.**

- **Tabla `sparring_games`, aparte de `games` y de `boards`.** Una partida de
  sparring no entra en estadísticas ni en detección de patrones porque no está
  donde esas consultas miran, sin necesidad de enseñarle a ninguna de ellas qué
  es una partida de entrenamiento.
- **Se guardan la posición de partida y las jugadas en UCI, nada más**
  (`starting_fen`, `moves_uci_json`). La posición actual, la lista en SAN, el
  PGN y si la partida acabó se derivan al servir con `lucia_core.sparring`.
- **`result` es la única marca de que la partida terminó** (`null` = en curso)
  y `termination` dice por qué: jaque mate, ahogado, material insuficiente,
  cincuenta jugadas, repetición o abandono.
- **El servidor valida las jugadas.** `POST /sparring/games/{id}/moves` rechaza
  con 422 lo que no sea legal en la posición actual o no toque, y en la misma
  respuesta devuelve la del motor.
- **Analizar una partida de sparring es abrirla como tablero** (RF-6.6, desde
  su PGN) y analizarla desde allí (RF-6.9). No hay `Analysis` colgado de
  `sparring_games`.
- **La fuerza del rival se configura fuera del núcleo**, en
  `lucia_api.services.sparring`, y no es la misma perilla en los dos motores:
  Stockfish acepta un Elo (`UCI_LimitStrength` + `UCI_Elo`, entre 1320 y 3190
  en Stockfish 17) y Lc0 no, porque su fuerza es la de la red Maia cargada.
  Por eso `engine_elo` es nullable y solo tiene valor con Stockfish.

## Razones

- **La frontera de RF-6.5 ya estaba trazada y funciona por construcción.** Lo
  que cuenta en estadísticas es lo que tiene fila en `games` con un análisis
  que la referencia (`latest_analysis_ids`). La opción 1 habría metido las
  partidas de sparring justo dentro de ese conjunto y habría obligado a añadir
  un `WHERE` de exclusión a cada consulta de RF-3, una por una, con el riesgo
  permanente de olvidarse en la siguiente que se escriba. Es el argumento de
  [ADR-0014](0014-tablero-propio-publicado-como-partida.md) leído al revés:
  allí se metió el tablero **en** `games` precisamente para que contara sin
  tocar ninguna consulta; aquí se deja fuera para que no cuente por el mismo
  motivo.
- **Y si algún día debe contar, el camino ya existe y es explícito.** Abrirla
  como tablero (RF-6.6) y, desde ahí, marcarla como partida propia (RF-6.5) es
  una decisión que toma quien juega, no un efecto colateral de haber
  entrenado. Eso adelanta además buena parte de lo que RF-11.3 pedirá para las
  partidas con ventaja.
- **La opción 2 habría metido en `boards` un documento que la API no puede
  seguir tratando como opaco.** Un tablero es un árbol de variantes que el
  servidor guarda sin leer; una partida de sparring es una línea única que el
  servidor tiene que entender para mover. Habría hecho falta un tablero con
  reglas a veces sí y a veces no, más un historial de deshacer que en una
  partida no significa nada: deshacer una jugada contra un rival es rehacer la
  partida, no restaurar una versión.
- **Un solo origen de verdad por partida.** De `starting_fen` +
  `moves_uci_json` sale todo; guardar además la posición actual, el PGN o un
  booleano "terminada" es tener el mismo hecho escrito dos veces y poder
  contradecirse. Es la misma razón por la que `AnalyzedMove` no guarda su SAN y
  por la que un tablero no guarda su posición actual aparte del árbol. El coste
  —rehacer el tablero en cada petición— es despreciable: una partida son
  decenas de jugadas.
- **`result` solo, sin booleano al lado.** Dos marcas de lo mismo se
  desincronizan; una sola no puede. Y `termination` va aparte porque "0-1" no
  distingue un mate de un abandono, que en un entrenamiento es justo lo que se
  quiere saber.
- **El servidor valida porque juega.** En el tablero de análisis la API guarda
  lo que le mandan y duplicar las reglas de chess.js en Python solo daría dos
  sitios donde equivocarse. Aquí no hay elección: para contestar hay que saber
  qué posición hay, y una jugada inventada por el navegador dejaría la partida
  en una posición que el motor no reconocería. El cliente sigue usando chess.js
  para saber qué arrastres permite, pero como comodidad de la interfaz, no como
  autoridad.
- **Las dos formas de tener un rival flojo no son la misma y no se pueden
  esconder tras una perilla común.** Stockfish busca igual de bien y se
  contiene: sus errores son los de un motor mutilado. Lc0 con Maia no se
  contiene —la red está entrenada para predecir la jugada de un humano de
  ~1500—, así que sus errores son los que comete la gente, y se juega a **un
  solo nodo** porque con más la búsqueda empieza a corregir a la red y se
  pierde justo lo que la hace humana. Fingir un Elo para Lc0 sería un
  deslizador que no mueve nada.

## Consecuencias

- **`EngineBridge` sabe jugar** (`play(board)`), además de analizar. Es la
  carencia que la nota técnica de RF-11 daba por pendiente y que RF-4.4
  ("re-juega desde el error") y RF-11.1 heredan resuelta. Como `analyze`, no se
  le pregunta por una posición terminal: no hay jugada que devolver y Lc0 se
  queda esperando para siempre ([ADR-0015](0015-cada-motor-con-su-unidad-de-esfuerzo-y-sus-opciones.md)).
- **Esto no contradice a ADR-0015, lo aplica.** Cada motor se sigue
  configurando en sus propios términos: Stockfish por tiempo y con opciones de
  fuerza, Lc0 por nodos y con su red. Lo nuevo es que la red del sparring
  (`MAIA_WEIGHTS`, `maia-1500.pb.gz`) es **otra** que la del análisis, y a
  propósito: Maia predice lo que jugaría una persona, que es exactamente lo que
  no se quiere de una fuente de verdad.
- **El motor se abre y se cierra en cada jugada**, como en
  `POST /analysis/position`. Un proceso vivo por partida habría que guardarlo,
  compartirlo entre peticiones y cerrarlo cuando la pestaña se abandona;
  arrancar cuesta milisegundos frente al segundo que tarda en pensar.
- **`starting_fen` es columna aunque hoy sea siempre la posición inicial.**
  RF-4.4 arranca desde la posición del blunder y RF-11.1 desde una posición
  elegida: cuando lleguen, no hay migración que hacer, y `to_pgn` ya escribe
  `[SetUp "1"]` + `[FEN ...]` en cuanto la partida no empieza en la estándar.
- **Una partida de sparring no tiene deshacer, ni variantes, ni barra de
  evaluación.** Lo primero porque no es un documento; lo último porque un rival
  calibrado se entrena jugando contra él, y una barra diciendo a cada jugada
  quién va ganando convierte la partida en un análisis asistido — el mismo
  motivo por el que los puzzles de RF-4.1 tampoco la tienen.
- **No hay reloj.** RF-4.3 no lo pide, y añadirlo obligaría a decidir qué pasa
  con una partida abandonada a mitad: hoy se retoma tal cual, que es lo que
  tiene sentido cuando entrenar se interrumpe.
- **Qué NO fija este ADR.** Qué motores se ofrecen, el rango de Elo aceptado
  (`STOCKFISH_ELO_RANGE`), cuánto piensa Stockfish por jugada
  (`STOCKFISH_MOVE_SECONDS`) y qué red Maia se carga son constantes con nombre
  y ajustes de `.env`, revisables sin tocar nada más. Mover las reglas al
  cliente o hacer que estas partidas cuenten en RF-3, en cambio, sí sería
  cambiar esta decisión.

## Ver también

- RF-4.3 en [02-requerimientos.md](../02-requerimientos.md), con las reglas
  concretas con las que se cumplió; RF-6.5 y RF-11.3, que trazan la misma
  frontera para los tableros y para las partidas con ventaja.
- [ADR-0013](0013-analisis-de-partida-o-de-tablero.md): por qué el árbol de un
  tablero es opaco para la API, que es la decisión que aquí se invierte y por
  qué.
- [ADR-0014](0014-tablero-propio-publicado-como-partida.md): el caso contrario
  —lo que sí entra en `games`— y el criterio que los separa.
- [ADR-0015](0015-cada-motor-con-su-unidad-de-esfuerzo-y-sus-opciones.md): cada
  motor en sus propios términos, del que la calibración de fuerza es una
  aplicación más.
- `packages/core/lucia_core/sparring/__init__.py` (las reglas puras),
  `packages/core/lucia_core/engine/bridge.py` (`play`),
  `apps/api/lucia_api/services/sparring.py` (la calibración y la partida),
  `apps/api/lucia_api/routers/sparring.py` (qué se manda y qué vuelve) y la
  tabla `sparring_games` en [03-arquitectura.md](../03-arquitectura.md).

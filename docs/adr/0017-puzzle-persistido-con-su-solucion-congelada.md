# ADR-0017 · El puzzle se persiste con su solución congelada y desacoplado de la jugada analizada de la que salió

**Estado:** aceptado · **Fecha:** 2026-09-19

## Contexto

RF-4.1 pide puzzles generados desde los errores propios, con repetición
espaciada, y RF-10.3 pide que acepten cualquier jugada equivalente a la mejor y
no solo la del motor. Las dos cosas se apoyan en material que ya estaba en la
base: los errores clasificados en `analyzed_moves` (RF-2.2) y las alternativas
del motor en la posición previa, en `alternatives_json` o rescatadas de
`position_cache` ([ADR-0007](0007-alternativas-por-jugada-json-y-cache.md)).

Visto así, un puzzle se parece mucho a un patrón de juego, y para los patrones
ya se decidió no persistir nada: se deducen al leer, sobre lo que el análisis
guardó ([ADR-0008](0008-patrones-deducidos-al-leer.md)). La pregunta era si un
puzzle podía seguir el mismo camino, y la respuesta corta es que no, porque
lleva encima un dato que un patrón no tiene: **el historial de repasos**.
Cuántas veces se acertó, cuándo fue el último, cuándo vuelve. Eso no se deduce
de ninguna otra fila: lo produce el usuario al entrenar, y es el único dato de
LUCIA que no se puede regenerar analizando otra vez.

Las opciones eran tres:

1. **Generar los puzzles al vuelo**, sin tabla, leyendo los errores como se
   leen los patrones, y guardar aparte solo el estado de repaso.
2. **Una tabla `puzzles` que enlace a la jugada** (`analyzed_move_id`), con la
   posición y la solución leídas de esa fila al servir, y en la tabla solo la
   clave foránea y el estado de SM-2.
3. **Una tabla `puzzles` que se guarde entera**: posición, jugada que se hizo,
   soluciones aceptadas, clasificación, coste del error y estado de SM-2, sin
   depender de la fila que la originó.

## Decisión

**La opción 3.** Existe la tabla `puzzles` y cada fila se basta a sí misma: el
FEN de antes del error, `played_uci`, `solutions_json` con todas las respuestas
aceptadas en UCI y de mejor a peor, la clasificación, la probabilidad de
victoria antes y después, y el estado de repetición espaciada (`repetitions`,
`interval_days`, `ease_factor`, `due_at`, `last_reviewed_at`).

No hay clave foránea a `analyzed_moves`. Lo único que ata el puzzle a su origen
es **de dónde salió**: `(game_id, ply)`, con restricción de unicidad, lo justo
para poder abrir la partida en el visor y para que regenerar no duplique nada.

`solutions_json` se calcula **una vez, al generar el puzzle**, con
`lucia_core.training.equivalent_solutions` (RF-10.3), y no se vuelve a tocar.
Servir un puzzle no consulta al motor, no lee `analyzed_moves` y no recalcula
nada: solo lee su fila.

Las reglas puras —SM-2 y la regla de equivalencia— viven en
`packages/core/lucia_core/training/`, como las de `insights`, y
`apps/api/lucia_api/services/training.py` es el puente con la base.

## Razones

- **El historial de repasos es el dato que no está en ninguna otra parte.** Un
  patrón mal deducido se corrige cambiando un umbral y volviendo a leer; un
  historial de repasos perdido no se recupera con nada. Eso solo ya obliga a
  una tabla propia, y una vez que la tabla existe, la pregunta deja de ser "¿se
  persiste?" y pasa a ser "¿cuánto se persiste?".
- **Recalcular las soluciones bajo un historial ya hecho falsearía ese
  historial.** SM-2 dice "este problema lo has acertado tres veces, vuelve en
  quince días". Si mañana se reanaliza la partida con otro motor o a otra
  profundidad y las jugadas aceptadas cambian, ese "tres veces" pasa a hablar
  de un problema que ya no es el que se contestó. El intervalo mide el recuerdo
  de una pregunta concreta; cambiar la pregunta y conservar la cuenta es
  mentirle al algoritmo, y con él al usuario.
- **La fila de la que sale el puzzle no es un ancla estable.** Reanalizar una
  partida —una segunda opinión con Lc0 (RF-2.6), otra profundidad— crea un
  `Analysis` nuevo con sus propias `analyzed_moves`, y la jugada original deja
  de ser la vigente: `latest_analysis_ids` mira el análisis más reciente, así
  que la opción 2 serviría puzzles construidos sobre un análisis que ya nadie
  enseña. Y `analyzed_moves.analysis_id` va con `ON DELETE CASCADE`: borrado
  el análisis, la fila desaparece y con ella el puzzle y su historial. Un
  historial de repasos no puede colgar de algo que se recrea cada vez que se
  vuelve a pasar el motor.
- **La opción 1 tiene el mismo problema y encima mueve la baraja sola.** Sin
  puzzle persistido, la cola de repaso se recalcularía en cada visita, y
  analizar una tanda de partidas cambiaría lo que toca hoy sin que el usuario
  lo pidiera. Con la tabla, generar es un acto explícito —`POST
  /training/puzzles`, el botón de la pantalla— y es idempotente: solo añade lo
  nuevo.
- **La cola se pide en SQL.** "Lo que vence hasta ahora, lo más atrasado
  primero, veinte como mucho" es un `WHERE` + `ORDER BY` + `LIMIT` sobre
  `due_at` indexada. Es exactamente la consecuencia que ADR-0008 anticipó al
  decir que no se puede filtrar por patrón en SQL y que RF-4.1 lo necesitaría.
- **Un puzzle abierto no puede viajar con nada que lo resuelva.** Al tener
  solución y coste del error en la fila, la comprobación es del servidor:
  `POST /training/puzzles/{id}/answer` recibe la jugada intentada y devuelve
  solución, jugada jugada, clasificación y probabilidades solo al cerrar el
  puzzle. Eso es además lo que permite aceptar cualquier jugada equivalente sin
  que el navegador tenga que saber cuáles son.
- **El coste de congelar es asumible.** Un puzzle guardado con las soluciones
  de un análisis a profundidad 18 puede quedarse por debajo de lo que hoy diría
  el motor. Es el precio de tener un historial honesto, y la salida es la
  misma que con cualquier dato envejecido: borrar el puzzle y regenerarlo, que
  es reconocer explícitamente que se está empezando ese repaso de cero.

## Consecuencias

- **Esto no contradice a ADR-0008, lo delimita.** Lo que se deduce al leer
  sigue deduciéndose al leer: los momentos críticos, los tipos de error, las
  tendencias. Lo que se persiste es lo que el usuario produce —el repaso— y lo
  que hace falta para que ese repaso siga significando lo mismo mañana. La
  línea es esa, y no "datos derivados sí / no".
- **La tabla puede quedarse desactualizada a propósito.** Reanalizar una
  partida no cambia sus puzzles. Es la decisión, no un descuido: si algún día
  se quiere refrescarlos, tendrá que ser una operación explícita que diga qué
  hace con el historial (reiniciarlo o arrastrarlo), y eso sería un ADR nuevo.
- **Borrar una partida se lleva sus puzzles** (`ON DELETE CASCADE` en
  `game_id`): sin la partida no se puede situar el error ni abrirlo en el
  visor, y un puzzle sin contexto no es un puzzle.
- **La calidad del puzzle depende de lo que había guardado al generarlo.** Con
  las alternativas de RF-10.1 se aceptan varias respuestas; con un análisis
  anterior cuyas posiciones ya no estén en `position_cache`, solo
  `best_move_uci`, una respuesta buena y ninguna equivalente. Un error del que
  no se pueda afirmar ninguna respuesta no genera puzzle. Se prefiere el hueco
  al puzzle falso, como en ADR-0008.
- **`lucia_core` sigue sin saber de bases de datos.** SM-2 recibe y devuelve un
  `SpacedRepetitionState` sin fechas —el intervalo en días, y quien persiste
  sabe qué hora es—, y la regla de equivalencia recibe pares
  `(jugada, probabilidad de victoria)`. Las dos se prueban solas (RNF-8), en
  `packages/core/tests/test_training.py`.
- **Qué NO fija este ADR.** Que el algoritmo sea SM-2, el margen de
  equivalencia (`EQUIVALENT_MOVE_MAX_WIN_PERCENT_LOSS`, hoy los mismos 2 puntos
  con los que la clasificación llama "excelente" a una jugada) y qué
  clasificaciones dan puzzle (`PUZZLE_CLASSIFICATIONS`) son constantes con
  nombre, revisables sin tocar nada más. Cambiar dónde y cuándo se calcula la
  solución, en cambio, sí es cambiar esta decisión.

## Ver también

- RF-4.1 y RF-10.3 en [02-requerimientos.md](../02-requerimientos.md), con las
  reglas concretas con las que se cumplieron.
- [ADR-0007](0007-alternativas-por-jugada-json-y-cache.md): de dónde salen las
  alternativas que se congelan como soluciones equivalentes.
- [ADR-0008](0008-patrones-deducidos-al-leer.md): la decisión contraria para
  los patrones, y la consecuencia donde ya se preveía que los puzzles sí se
  persistirían.
- `packages/core/lucia_core/training/__init__.py` (las reglas),
  `apps/api/lucia_api/services/training.py` (el puente con la base),
  `apps/api/lucia_api/routers/training.py` (qué se manda y qué no) y la tabla
  `puzzles` en [03-arquitectura.md](../03-arquitectura.md).

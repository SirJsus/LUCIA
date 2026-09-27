# ADR-0021 · El plan semanal se deduce en cada visita, y el orden de las debilidades es editorial y no numérico

**Estado:** aceptado · **Fecha:** 2026-09-21

## Contexto

RF-4.5 pide un "plan de entrenamiento semanal generado a partir de las
debilidades detectadas". Es el último requerimiento de RF-4 y llega cuando ya
existe todo el material del que tendría que salir:

- **Qué falla** está resuelto desde RF-3: dónde se pierde ventaja (RF-3.3), de
  qué tipo son los errores (RF-3.4), qué aperturas cuestan puntos (RF-3.2),
  qué pasa cuando baja el reloj (RF-3.5) y si se mejora mes a mes (RF-3.7).
- **Qué hacer al respecto** está resuelto desde RF-4.1 a RF-4.4: puzzles,
  líneas de apertura, posiciones que re-jugar y partidas contra el motor, cada
  una con su cola y su pantalla.

Lo que no estaba decidido era cómo se juntan, y juntarlos tiene cuatro
preguntas con respuesta no obvia:

1. **¿El plan se guarda?** Es la tercera vez que el proyecto se hace esta
   pregunta, y las dos anteriores se respondieron en sentidos contrarios: los
   patrones se deducen al leer
   ([ADR-0008](0008-patrones-deducidos-al-leer.md)) y los puzzles se persisten
   con su solución congelada
   ([ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md)). Un plan
   "de la semana" suena a algo que se fija el lunes y se consulta hasta el
   domingo, es decir, a tabla.
2. **¿Quién marca que un deber está hecho?** La lectura literal pide una
   casilla que marcar, y con ella una tabla de progreso semanal.
3. **¿En qué orden se enseñan las debilidades?** Las cinco clases llegan con
   un número, pero **cada número está en una unidad distinta**: puntos de
   probabilidad de victoria por jugada, porcentaje de los errores, puntos de
   marcador perdidos en una apertura, porcentaje de partidas con apuros de
   reloj y puntos de precisión. Ordenar por él es lo primero que se le ocurre
   a cualquiera que lea el código.
4. **¿Cuánto se pide de cada cosa?** Un plan semanal necesita una cifra, y esa
   cifra puede salir de lo que "debería" entrenarse o de lo que de verdad hay
   para entrenar.

## Decisión

**El plan no se guarda, cada tarea nace de una debilidad concreta y la lleva
encima, las debilidades se ordenan por clase y no por número, y el objetivo de
cada tarea nunca pide más material del que hay.**

- **No hay tabla ni migración.** `GET /training/plan`
  (`lucia_api.services.plan`) recalcula el plan entero en cada visita a partir
  de `get_player_stats` (RF-3) y de las colas de RF-4. RF-4.5 es el único
  requerimiento de RF-4 que no toca el modelo de datos.
- **El avance sale de fechas que la base ya guarda**:
  `puzzles.last_reviewed_at`, `opening_drills.last_reviewed_at` y
  `sparring_games.created_at` (con `origin_game_id` para separar lo re-jugado
  del sparring a secas). Nadie marca nada a mano: entrenar en las otras
  pestañas es lo que mueve la barra.
- **Cada tarea viaja con sus `weaknesses`**, las debilidades que la piden, y la
  tabla que las une es `_TASK_BY_WEAKNESS` en `lucia_core.plan`. Una
  debilidad sin entrenamiento posible no genera deber, y un deber sin
  debilidad detrás no existe.
- **El orden de las debilidades es fijo por clase**: fase, tipo de error,
  apertura, apuros de reloj y tendencia. Es editorial —de lo más estructural a
  lo más circunstancial— y está escrito en el cuerpo de `detect_weaknesses`,
  no en un `sort`. `magnitude` sirve para decir cuánto hay de algo y para
  compararlo con el umbral de su propia clase; **nunca para comparar dos
  clases entre sí**.
- **`weekly_target` = `min(MAX_WEEKLY_TARGETS[tarea], material disponible)`**,
  y una tarea sin material no se emite. Puzzles y líneas cuentan como material
  **solo lo que vence esta semana**; sparring no tiene material que agotar, así
  que su techo es su propio tope semanal.
- **La semana empieza el lunes** (`week_start`), no "hace siete días".
- **El plan es la portada de Entrenamiento**: `/training` es el plan y los
  puzzles pasan a `/training/puzzles` (`PuzzlesPage`, antes `TrainingPage`).

## Razones

- **Un plan congelado envejece en cuanto se analiza una partida más.** Es el
  mismo argumento de ADR-0008: lo que solo es una lectura de lo que ya hay se
  deduce al leer. Y aquí se ve más claro que en ningún sitio, porque el plan es
  una lectura **de segundo orden** —de las estadísticas, que ya son una lectura
  de los análisis—; guardarlo dejaría una copia que puede contradecir a la
  pantalla de Estadísticas abierta en la pestaña de al lado. La regla que
  separa esta decisión de ADR-0017 sigue siendo la misma: **se persiste lo que
  lleva estado propio**, y el plan no lleva ninguno.
- **La casilla que marcar sería un dato que ya existe, escrito dos veces.** Si
  hay que marcar "hechos 5 puzzles" y además `puzzles.last_reviewed_at` dice
  cuándo se repasó cada uno, las dos fuentes se desincronizan a la primera
  (repasar sin marcar, marcar sin repasar). Derivándolo de las fechas, el
  avance es **lo que se hizo** por definición, y no hay forma de mentirle al
  plan ni de olvidarse de marcarlo.
- **Cada deber lleva su motivo porque el requerimiento dice "a partir de las
  debilidades detectadas".** Un objetivo semanal sin la debilidad a la vista es
  una cuota inventada: quien entrena no puede discutirla, ni entender por qué
  cambia de una semana a otra, ni saber qué dejará de aparecer cuando el
  problema se arregle. Por eso `weaknesses` viaja en la respuesta y se pinta en la
  tarjeta, no en un tooltip.
- **Ordenar por `magnitude` sería inventar una escala común que no existe.**
  "Pierdo 8 puntos de probabilidad de victoria por jugada en el medio juego" y
  "el 55 % de mis errores son tácticos" no son cantidades comparables: el
  segundo número es más grande y dice bastante menos. Un `sort` por ese campo
  daría un orden que parece calculado y es arbitrario, y lo pondría **primero**
  en pantalla bajo la insignia "lo primero". El orden por clase, en cambio, se
  puede defender con una frase: primero dónde se pierde la partida, luego por
  qué se pierde, luego en qué apertura concreta, y al final los hábitos. Es una
  decisión de criterio, no un cálculo, y queda escrita como tal.
  Esto se corrigió durante la revisión de la tarea: los comentarios prometían
  un orden "por gravedad" que el código nunca hizo. Se arregló el comentario y
  no el código, a propósito.
- **Un plan que pide treinta puzzles cuando hay cuatro no es exigente, es
  falso.** Un objetivo inalcanzable enseña que el plan no mira lo que hay, y a
  partir de ahí no se le hace caso a ninguno. Acotar por el material disponible
  cuesta un `min` y hace que el 100 % de la barra sea siempre alcanzable.
- **Contar como material solo lo que vence esta semana respeta al SM-2.**
  Repasar un puzzle antes de tiempo no es entrenar, es adelantar trabajo que la
  repetición espaciada ya había colocado en otra fecha; meterlo en el objetivo
  semanal sería empujar a hacerlo.
- **Con una ventana móvil, el avance bajaría solo.** "Los últimos siete días"
  haría que lo entrenado el lunes dejara de contar el martes siguiente: la
  barra retrocedería sin que nadie hiciera nada. Con el lunes como corte, el
  plan es el mismo toda la semana y empieza de cero cuando la semana empieza de
  cero.
- **El plan es la portada porque es la pantalla que dice por dónde empezar.**
  Entrar en Entrenamiento y caer en los puzzles daba por hecho que la respuesta
  a "¿qué entreno hoy?" es siempre la misma; las otras cuatro pestañas son
  adónde te manda el plan.

## Consecuencias

- **RF-4.5 no añade tabla, migración ni endpoint de escritura.** El único
  endpoint es `GET /training/plan`, de solo lectura. Es la primera
  funcionalidad de entrenamiento que no toca el esquema.
- **El plan tiene dos vacíos distintos y hay que saber cuál es cuál.** Sin
  partidas analizadas (`analyzed_games == 0`) no se sabe nada y la pantalla
  manda a analizar; con partidas analizadas y sin debilidades por encima de su
  umbral, el plan está vacío **porque no hay nada que arreglar**. Por eso
  `analyzed_games` viaja en la respuesta: sin él, "no tienes debilidades" sería
  una felicitación inventada.
- **Los cinco umbrales (`MIN_*`) y los cuatro topes (`MAX_WEEKLY_TARGETS`) son
  constantes con nombre** en `lucia_core.plan`, ajustables sin tocar este ADR
  ni el requerimiento. Lo que sí sería cambiar esta decisión: persistir el
  plan, añadir una forma de marcar un deber a mano, ordenar las debilidades por
  `magnitude` o pedir más de lo que hay.
- **`magnitude` es un contrato frágil y está documentado como tal** en el
  núcleo, en `WeaknessOut` y en `shared-types`. La pantalla lo formatea en
  cinco unidades distintas (`formatWeaknessSentence`), y ese es el único sitio
  donde se decide cómo se lee cada clase.
- **Añadir una sexta clase de debilidad o una quinta forma de entrenar es
  añadir una fila.** `detect_weaknesses` decide si entra, `_TASK_BY_WEAKNESS`
  a qué entrenamiento lleva y `TASK_DISPLAYS` cómo se lee; nada más cambia. El
  precio de que el orden sea editorial es que una clase nueva obliga a decidir
  dónde va, que es justamente la decisión que no queremos que tome un `sort`.
- **`/training` cambia de significado.** Cualquier enlace o marcador que
  apuntara a los puzzles ahora abre el plan; los puzzles viven en
  `/training/puzzles`. La sub-navegación pasa a cinco pestañas y por eso
  envuelve en pantallas estrechas.

## Ver también

- RF-4.5 en [02-requerimientos.md](../02-requerimientos.md), con las reglas
  concretas con las que se cumplió y el cierre de RF-4 entero.
- [ADR-0008](0008-patrones-deducidos-al-leer.md) y
  [ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md): las dos
  respuestas contrarias a "¿esto se guarda?" y el criterio que las separa;
  [ADR-0020](0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md)
  aplicó ese mismo criterio a la lista de re-jugar.
- [ADR-0019](0019-el-drill-de-aperturas-se-construye-sobre-las-salidas-de-la-teoria.md):
  de dónde sale `points_lost`, la unidad con la que el plan mide una apertura.
- `packages/core/lucia_core/plan/__init__.py` (umbrales, orden y tabla de
  entrenamientos), `apps/api/lucia_api/services/plan.py` (de dónde salen los
  números y el avance), `apps/api/lucia_api/routers/plan.py`,
  `apps/web/src/features/training/PlanPage.tsx` y `plan.ts`, y el flujo 15 de
  [03-arquitectura.md](../03-arquitectura.md).

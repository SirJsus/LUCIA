# `features/training`

RF-4 entero: el **plan de entrenamiento semanal** (RF-4.5), que es la portada
de la sección, y las cuatro formas de entrenar a las que manda — puzzles
sacados de los errores propios (RF-4.1, con RF-10.3), el drill de aperturas
(RF-4.2), sparring contra el motor con la fuerza calibrada (RF-4.3) y re-jugar
desde el error (RF-4.4). Las cinco pestañas cuelgan de la misma sección y
comparten cabecera (`TrainingHeader`); la elección entre ellas vive dentro, no
en la navegación principal. La sexta pantalla, la de una partida de sparring
concreta, se encabeza como pantalla de detalle —vuelta atrás sobre el título de
lo que se tiene delante, como el visor y el tablero de análisis— y no lleva la
sub-navegación (fila 94 del inventario de docs/07-coherencia-ui.md).

| Archivo                   | Qué es                                                                                                                                                                                                                                                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TrainingHeader.tsx`      | La cabecera común: el título de la sección, la frase de cada pantalla (`children`) y la sub-navegación Plan \| Puzzles \| Aperturas \| Re-jugar \| Sparring. El plan va primero porque es la portada.                                                                                                                       |
| `PlanPage.tsx`            | El plan de la semana (RF-4.5) y **la portada de la sección** (`/training`): arriba qué te está costando puntos, debajo los deberes que salen de ahí, cada uno con su avance y con las debilidades que lo piden. No se hace nada aquí: cada tarjeta lleva a la pestaña donde se entrena.                                     |
| `plan.ts`                 | Cómo se lee el plan: cada debilidad en una frase con su número en **su** unidad (`formatWeaknessSentence`) y cómo se llama cada deber, en qué se cuenta y adónde lleva (`TASK_DISPLAYS`). Pura, probada en `__tests__/plan.test.ts`.                                                                                        |
| `PuzzlesPage.tsx`         | Puzzles: el botón de generar, la cola del día y los estados por los que pasa (sin puzzles, por hoy terminado, resolviendo).                                                                                                                                                                                                 |
| `PuzzleSolver.tsx`        | Un puzzle: el tablero donde se responde, la capa de ocupación bajo él (RF-7, ver abajo) y el panel que dice cómo fue. Se monta con `key={puzzle.id}`, así que cambiar de puzzle reinicia su estado. La capa lee la posición **que se está viendo**, que tras fallar es la del intento y no la del puzzle.                   |
| `arrows.ts`               | Las flechas del puzzle cerrado: solución en verde, equivalentes atenuadas, la jugada de la partida en rojo. Pura, probada en `__tests__/arrows.test.ts`.                                                                                                                                                                    |
| `DrillsPage.tsx`          | Drill de aperturas: el botón de generar líneas —con el aviso de cuánta teoría falta por consultar—, la cola del día y los estados por los que pasa (sin líneas, por hoy terminado, recorriendo una).                                                                                                                        |
| `DrillRunner.tsx`         | Una línea: el tablero donde se repite jugando el propio bando, la capa de ocupación bajo él (RF-7, ver abajo) y el panel que dice qué se entrena y por qué. Se monta con `key={drill.id}`, así que cambiar de línea reinicia su estado.                                                                                     |
| `drills.ts`               | Cómo se lee un drill: el motivo en palabras ("Abandonas la teoría aquí en 8 partidas y sacas un 25,0 %") y cuántas jugadas propias tiene la línea. Pura, probada en `__tests__/drills.test.ts`.                                                                                                                             |
| `ReplaysPage.tsx`         | Re-jugar desde el error (RF-4.4): la lista curada de tus errores más caros y, bajo el que elijas, el formulario para retomar la partida desde ahí. La lista **no se guarda en ninguna parte**: sale de los análisis cada vez que se pide.                                                                                   |
| `SparringSetupForm.tsx`   | Elegir rival, bando y fuerza. Extraído de `SparringPage` al necesitarlo también `ReplaysPage` y el visor: las tres pantallas desde las que se abre una partida contra el motor eligen la dificultad con los mismos controles, el mismo orden y las mismas explicaciones (criterio C-2). Solo cambia cómo se llama el botón. |
| `SparringPage.tsx`        | Sparring, la antesala: elegir rival, color y fuerza para empezar, y el listado para retomar lo que quedó a medias — con las partidas re-jugadas (RF-4.4) marcadas con una insignia, porque son de la misma tabla.                                                                                                           |
| `SparringGamePage.tsx`    | Una partida de sparring en marcha: el tablero donde se juega, la capa de ocupación bajo él (RF-7, ver abajo) y el panel con el rival, las jugadas y cómo acabó. También las retomadas (RF-4.4), que añaden de dónde salieron con enlace de vuelta al visor.                                                                 |
| `TrainingStatusBadge.tsx` | La insignia del panel lateral de las tres pantallas con tablero: si el sistema está esperando, si te toca o si el ejercicio se acabó. Dice lo mismo en las tres, que antes significaba el repaso en el puzzle, la baraja en el drill y el turno en el sparring (fila 98 del inventario de docs/07-coherencia-ui.md).        |
| `sparring.ts`             | Cómo se lee una partida en pantalla: el resultado desde quien juega ("Ganaste por jaque mate"). Pura, probada en `__tests__/sparring.test.ts`. Emparejar las jugadas por turno es `turnsOf`, en `lib/moves.ts`, que es de donde sale también la lista del visor.                                                            |
| `TrainingBoard.tsx`       | La columna del tablero de las tres pantallas con tablero: el tablero, la capa de ocupación (RF-7) y la frase de pie con los atajos. Cada una pone la posición, quién puede mover y su propia frase; lo demás —sin barra de evaluación, marcas apagadas— es igual en las tres a propósito (criterios C-1 y C-2).             |
| `useReviewQueue.ts`       | El ciclo de las dos pantallas de repaso (puzzles y aperturas): la tanda del día, ir al siguiente y generar más. Lo que cada una dice no pasa por aquí.                                                                                                                                                                      |

**Por qué dos esperas no dicen «Cargando…».** Las pantallas que traen algo ya
guardado lo anuncian así —«Cargando tus puzzles…», «Cargando tus líneas…»,
«Cargando tus partidas de sparring…», como el resto de la aplicación—, pero el
plan (`PlanPage`) y la lista de re-jugar (`ReplaysPage`) no traen nada
guardado: las dos se deducen al leer, recorriendo los análisis. Por eso dicen
«Mirando tus partidas…» y «Buscando tus errores…», que es lo que de verdad está
pasando; llamarlo cargar prometería una lista que existía de antes. Es una
divergencia deliberada del criterio C-2 de docs/07-coherencia-ui.md, no un
descuido: lo que se comparte es que la espera **siempre** se nombra, nunca que
se nombre con el mismo verbo.

**Lo que la pantalla de puzzles no sabe.** Ni la solución ni la jugada que se
hizo en la partida llegan al navegador mientras el puzzle está abierto: las dos
lo resuelven. Se comprueba en el servidor (`POST
/training/puzzles/{id}/answer`), que además es quien sabe qué jugadas son
equivalentes a la mejor (RF-10.3) y quien anota el repaso. Aquí solo se manda
la jugada intentada y se cuentan los intentos, que es lo que distingue después
acertar a la primera de acertar tropezando.

**En el drill de aperturas la línea tampoco está aquí, y por partida doble.**
Mientras el drill está abierto, el navegador solo sabe la posición que tiene
delante: manda cada jugada a `POST /training/drills/{id}/moves` y el servidor
comprueba, **contesta por el rival** y devuelve la posición siguiente; la línea
entera y el próximo repaso llegan al cerrarlo. Si viajara, el navegador no solo
sabría la respuesta, sabría además qué va a jugar el otro. Lo que sí lleva esta
pantalla es **por dónde va** (`ply`) y cuántas veces se ha fallado, como
`PuzzleSolver` lleva el número de intento: el servidor no guarda progreso
porque un drill se repite entero o no se repite. De dónde salen las líneas
—las salidas de la teoría de RF-3.6, corregidas con la jugada de maestros— y
por qué "peor" se mide en puntos perdidos está en
[ADR-0019](../../../../../docs/adr/0019-el-drill-de-aperturas-se-construye-sobre-las-salidas-de-la-teoria.md).

**En sparring el servidor es el rival y también el árbitro.** La partida no se
guarda aquí: se manda la jugada a `POST /sparring/games/{id}/moves` y vuelve el
estado entero —posición, jugadas, resultado— con la respuesta del motor ya
dentro, así que la pantalla no reconcilia nada y recargar a mitad la deja donde
estaba. Es la diferencia con el tablero de análisis (RF-6), donde quien sabe de
reglas es chess.js y la API solo custodia el árbol; aquí chess.js se usa para
saber qué arrastres se permiten, como comodidad, no como autoridad. Cada
partida tiene URL propia (`/training/sparring/$sparringGameId`) porque vive en
la base y se retoma. Razonado en
[ADR-0018](../../../../../docs/adr/0018-sparring-en-su-propia-tabla-y-el-servidor-como-arbitro.md).

**Re-jugar desde el error no es una cuarta forma de jugar, es sparring
empezado en otra posición.** `ReplaysPage` **solo elige**: retomar abre una
partida de `sparring_games` con su `origin`, y desde ahí se juega en
`SparringGamePage` como cualquier otra. Por eso la insignia "re-jugada" en el
listado de Sparring y no una lista aparte. Hay **dos puertas** a lo mismo, a
propósito: esta pestaña responde "¿por dónde empiezo?" con los errores graves
más caros, y el botón "Jugar desde aquí" del visor retoma **cualquier**
posición de cualquier partida propia. Las dos usan `SparringSetupForm` y el
mismo endpoint, así que no hay dos formas de elegir dificultad que mantener.
**La lista no se guarda**: se deduce de los análisis al leer, como los patrones
de RF-3, porque no arrastra repasos ni progreso — es la decisión contraria a la
de los puzzles y los drills. Y **lo que costó el error se enseña abierto**, al
revés que en un puzzle sin resolver: aquí no hay nada que adivinar, y es el
dato que dice por cuál empezar. Razonado en
[ADR-0020](../../../../../docs/adr/0020-re-jugar-desde-el-error-es-sparring-desde-otra-posicion.md),
incluido por qué esto no invade RF-11.1 (jugar desde una posición inventada,
congelado fuera de v1.0): la posición la deriva siempre el servidor del PGN
guardado, nunca llega como FEN, y no hay perilla de ventaja material.

**Por qué aquí no hay barra de evaluación**, al contrario que el visor y el
tablero de análisis: en un puzzle, la evaluación de la posición es media
respuesta —los números aparecen al cerrarlo, en el panel, con lo que costó el
error—; en un drill lo que se entrena es recordar la línea, y una evaluación en
pantalla la delata; en sparring, una barra diciendo a cada jugada quién va
ganando convierte la partida en un análisis asistido. Para analizar una partida de
sparring está el camino de siempre: abrirla como tablero desde su PGN (RF-6.6)
y analizarla desde ahí (RF-6.9), que la deja fuera de las estadísticas por
construcción.

**Y por qué sí hay capa de ocupación** (RF-7.1 a RF-7.7, desde el 2026-09-22),
que es la otra cara de lo anterior. La barra de evaluación es la opinión del
motor sobre la posición; la ocupación es la lectura de la posición que ya está
en pantalla —quién ataca y quién defiende cada casilla, sin motor, sin API y
sin guardar nada—, y RF-7 dice desde su cabecera que se activa sobre
**cualquier** tablero, entrenamiento incluido. Está en las tres pantallas que
tienen tablero: el puzzle, la línea del drill y la partida de sparring. El
plan, la lista de re-jugar y la antesala de sparring no tienen tablero y quedan
fuera. Ninguna de las tres calcula nada: le pasan el FEN de la posición que hay
delante a `useOccupancy` y le dan el controlador a `Chessboard` por su
propiedad `occupancyController`; todo lo demás vive en `components/board/`,
compartido con el visor y el tablero de análisis, y la frase que anuncia el
atajo `O` es la misma constante en las cinco
(`components/board/hints.ts::OCCUPANCY_TOGGLE_KEY_HINT`). La frontera entre lo
que entra aquí y lo que no —lo que se lee de la posición que hay en pantalla
sí, lo que es opinión del motor no— está razonada, con lo que se descartó, en
[ADR-0023](../../../../../docs/adr/0023-la-ocupacion-entra-en-el-entrenamiento-y-la-barra-no.md).

**Aquí las tres marcas arrancan apagadas** (`marksOnByDefault: false`), y es lo
único que distingue esta capa de la del visor y la del tablero de análisis,
donde arrancan encendidas. Rodear las piezas colgadas (RF-7.4) es media
solución de un puzzle táctico y, durante una partida de sparring, el aviso de
blunder que un rival calibrado no debe dar; las clavadas (RF-7.6) y los rayos X
(RF-7.5) se apagan con ellas —y no solo las que delatan— porque el panel las
presenta como tres controles iguales. Siguen estando en el panel, con su ayuda,
y el propio panel dice ahí que arrancan apagadas y por qué: quien las quiera
las enciende a sabiendas, que es el matiz entre leer la posición y que te la
lean. También en
[ADR-0023](../../../../../docs/adr/0023-la-ocupacion-entra-en-el-entrenamiento-y-la-barra-no.md).

**El plan no se guarda, y sus deberes se marcan solos.** `PlanPage` solo lee:
`GET /training/plan` recalcula el plan en cada visita a partir de las
estadísticas (RF-3) y de las colas de estas mismas pestañas, y lo que llevas
hecho sale de fechas que la base ya guarda —los puzzles y las líneas repasados
desde el lunes, las partidas jugadas desde el lunes—. No hay casilla que
marcar: entrenar en las otras pestañas es lo que mueve la barra. Tres cosas que
conviene saber al leer esta pantalla: **(a)** cada deber enseña la debilidad
que lo pide, porque un objetivo sin motivo a la vista sería una cuota
inventada; **(b)** el orden de las debilidades —y con él la insignia "lo
primero"— es fijo por clase y **no** va de mayor a menor número: los cinco
números están en cinco unidades distintas y no se pueden comparar; y **(c)** el
objetivo nunca pide más material del que hay, así que el 100 % siempre es
alcanzable. Razonado en
[ADR-0021](../../../../../docs/adr/0021-el-plan-semanal-se-deduce-y-el-orden-de-las-debilidades-es-editorial.md).

Cuándo vuelve cada puzzle **y cada línea** lo decide el mismo SM-2 de
`lucia_core.training` —un drill se repasa como se repasa un puzzle, así que no
hay dos comportamientos que explicar—, las reglas de una línea están en
`lucia_core.drills` y las de una partida en `lucia_core.sparring` —incluido
`board_at_ply`, que saca del PGN la posición desde la que se retoma—, y las
del plan en `lucia_core.plan` —qué cuenta como debilidad y qué entrenamiento le
toca—. Con RF-4.5 **RF-4 queda cerrado entero**: esta carpeta ya no tiene nada
pendiente.

# `features/training`

Las cuatro formas de entrenar que ya existen (RF-4): puzzles sacados de los
errores propios (RF-4.1, con RF-10.3), el drill de aperturas (RF-4.2),
sparring contra el motor con la fuerza calibrada (RF-4.3) y re-jugar desde el
error (RF-4.4). Las cinco pantallas —las cuatro más la de una partida de
sparring— cuelgan de la misma sección y comparten cabecera; la elección entre
ellas vive dentro, no en la navegación principal.

| Archivo | Qué es |
| --- | --- |
| `TrainingHeader.tsx` | La cabecera común: el título de la sección, la frase de cada pantalla (`children`) y la sub-navegación Puzzles \| Aperturas \| Re-jugar \| Sparring. |
| `TrainingPage.tsx` | Puzzles: el botón de generar, la cola del día y los estados por los que pasa (sin puzzles, por hoy terminado, resolviendo). |
| `PuzzleSolver.tsx` | Un puzzle: el tablero donde se responde y el panel que dice cómo fue. Se monta con `key={puzzle.id}`, así que cambiar de puzzle reinicia su estado. |
| `arrows.ts` | Las flechas del puzzle cerrado: solución en verde, equivalentes atenuadas, la jugada de la partida en rojo. Pura, probada en `__tests__/arrows.test.ts`. |
| `DrillsPage.tsx` | Drill de aperturas: el botón de generar líneas —con el aviso de cuánta teoría falta por consultar—, la cola del día y los estados por los que pasa (sin líneas, por hoy terminado, recorriendo una). |
| `DrillRunner.tsx` | Una línea: el tablero donde se repite jugando el propio bando y el panel que dice qué se entrena y por qué. Se monta con `key={drill.id}`, así que cambiar de línea reinicia su estado. |
| `drills.ts` | Cómo se lee un drill: el motivo en palabras ("Abandonas la teoría aquí en 8 partidas y sacas un 25,0 %") y cuántas jugadas propias tiene la línea. Pura, probada en `__tests__/drills.test.ts`. |
| `ReplaysPage.tsx` | Re-jugar desde el error (RF-4.4): la lista curada de tus errores más caros y, bajo el que elijas, el formulario para retomar la partida desde ahí. La lista **no se guarda en ninguna parte**: sale de los análisis cada vez que se pide. |
| `SparringSetupForm.tsx` | Elegir rival, bando y fuerza. Extraído de `SparringPage` al necesitarlo también `ReplaysPage` y el visor: las tres pantallas desde las que se abre una partida contra el motor eligen la dificultad con los mismos controles, el mismo orden y las mismas explicaciones (criterio C-2). Solo cambia cómo se llama el botón. |
| `SparringPage.tsx` | Sparring, la antesala: elegir rival, color y fuerza para empezar, y el listado para retomar lo que quedó a medias — con las partidas re-jugadas (RF-4.4) marcadas con una insignia, porque son de la misma tabla. |
| `SparringGamePage.tsx` | Una partida de sparring en marcha: el tablero donde se juega y el panel con el rival, las jugadas y cómo acabó. También las retomadas (RF-4.4), que añaden de dónde salieron con enlace de vuelta al visor. |
| `sparring.ts` | Cómo se lee una partida en pantalla: el resultado desde quien juega ("Ganaste por jaque mate") y las jugadas emparejadas por turno. Pura, probada en `__tests__/sparring.test.ts`. |

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

Cuándo vuelve cada puzzle **y cada línea** lo decide el mismo SM-2 de
`lucia_core.training` —un drill se repasa como se repasa un puzzle, así que no
hay dos comportamientos que explicar—, las reglas de una línea están en
`lucia_core.drills` y las de una partida en `lucia_core.sparring` —incluido
`board_at_ply`, que saca del PGN la posición desde la que se retoma—. Del
entrenamiento queda pendiente el plan semanal (RF-4.5) — ver
[`docs/05-roadmap.md`](../../../../../docs/05-roadmap.md).

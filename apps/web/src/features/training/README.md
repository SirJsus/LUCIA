# `features/training`

Las tres formas de entrenar que ya existen (RF-4): puzzles sacados de los
errores propios (RF-4.1, con RF-10.3), el drill de aperturas (RF-4.2) y
sparring contra el motor con la fuerza calibrada (RF-4.3). Las cuatro pantallas
—las tres más la de una partida de sparring— cuelgan de la misma sección y
comparten cabecera; la elección entre ellas vive dentro, no en la navegación
principal.

| Archivo | Qué es |
| --- | --- |
| `TrainingHeader.tsx` | La cabecera común: el título de la sección, la frase de cada pantalla (`children`) y la sub-navegación Puzzles \| Aperturas \| Sparring. |
| `TrainingPage.tsx` | Puzzles: el botón de generar, la cola del día y los estados por los que pasa (sin puzzles, por hoy terminado, resolviendo). |
| `PuzzleSolver.tsx` | Un puzzle: el tablero donde se responde y el panel que dice cómo fue. Se monta con `key={puzzle.id}`, así que cambiar de puzzle reinicia su estado. |
| `arrows.ts` | Las flechas del puzzle cerrado: solución en verde, equivalentes atenuadas, la jugada de la partida en rojo. Pura, probada en `__tests__/arrows.test.ts`. |
| `DrillsPage.tsx` | Drill de aperturas: el botón de generar líneas —con el aviso de cuánta teoría falta por consultar—, la cola del día y los estados por los que pasa (sin líneas, por hoy terminado, recorriendo una). |
| `DrillRunner.tsx` | Una línea: el tablero donde se repite jugando el propio bando y el panel que dice qué se entrena y por qué. Se monta con `key={drill.id}`, así que cambiar de línea reinicia su estado. |
| `drills.ts` | Cómo se lee un drill: el motivo en palabras ("Abandonas la teoría aquí en 8 partidas y sacas un 25,0 %") y cuántas jugadas propias tiene la línea. Pura, probada en `__tests__/drills.test.ts`. |
| `SparringPage.tsx` | Sparring, la antesala: elegir rival, color y fuerza para empezar, y el listado para retomar lo que quedó a medias. |
| `SparringGamePage.tsx` | Una partida de sparring en marcha: el tablero donde se juega y el panel con el rival, las jugadas y cómo acabó. |
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
`lucia_core.drills` y las de una partida en `lucia_core.sparring`. Del
entrenamiento quedan pendientes "re-juega desde el error" (RF-4.4) y el plan
semanal (RF-4.5) — ver
[`docs/05-roadmap.md`](../../../../../docs/05-roadmap.md).

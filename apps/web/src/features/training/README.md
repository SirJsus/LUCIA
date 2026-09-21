# `features/training`

Las dos formas de entrenar que ya existen (RF-4): puzzles sacados de los
errores propios (RF-4.1, con RF-10.3) y sparring contra el motor con la fuerza
calibrada (RF-4.3). Las tres pantallas cuelgan de la misma sección y comparten
cabecera; la elección entre ellas vive dentro, no en la navegación principal.

| Archivo | Qué es |
| --- | --- |
| `TrainingHeader.tsx` | La cabecera común: el título de la sección, la frase de cada pantalla (`children`) y la sub-navegación Puzzles \| Sparring. |
| `TrainingPage.tsx` | Puzzles: el botón de generar, la cola del día y los estados por los que pasa (sin puzzles, por hoy terminado, resolviendo). |
| `PuzzleSolver.tsx` | Un puzzle: el tablero donde se responde y el panel que dice cómo fue. Se monta con `key={puzzle.id}`, así que cambiar de puzzle reinicia su estado. |
| `arrows.ts` | Las flechas del puzzle cerrado: solución en verde, equivalentes atenuadas, la jugada de la partida en rojo. Pura, probada en `__tests__/arrows.test.ts`. |
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
error—; en sparring, una barra diciendo a cada jugada quién va ganando
convierte la partida en un análisis asistido. Para analizar una partida de
sparring está el camino de siempre: abrirla como tablero desde su PGN (RF-6.6)
y analizarla desde ahí (RF-6.9), que la deja fuera de las estadísticas por
construcción.

Cuándo vuelve cada puzzle lo decide SM-2 en `lucia_core.training` y las reglas
de una partida están en `lucia_core.sparring`. Del entrenamiento quedan
pendientes el drill de aperturas (RF-4.2), "re-juega desde el error" (RF-4.4) y
el plan semanal (RF-4.5) — ver
[`docs/05-roadmap.md`](../../../../../docs/05-roadmap.md).

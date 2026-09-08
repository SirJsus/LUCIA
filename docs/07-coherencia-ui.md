# 07 · Coherencia de interfaz

Este documento existe porque la aplicación creció pantalla a pantalla y cada
una resolvió a su manera cosas que deberían resolverse igual en todas. El
síntoma que lo motivó: en el detalle de una partida se navega con botones en
pantalla y la interfaz cambia según lo que esté haciendo el motor, mientras
que en el tablero de análisis se navega solo con el teclado y la pantalla es
siempre la misma. Quien ya sabe de análisis de partidas se adapta; quien no,
lee el tablero de análisis como una herramienta tosca.

**Qué es cada mitad de este documento.** Los criterios C-1 a C-7 son
**RNF-11**, que vive en la sección Post 1.0 de
[docs/02-requerimientos.md](02-requerimientos.md): son una práctica de trabajo
vinculante desde hoy en cada commit de `apps/web`, no una prestación que se
entregue en v1.0, y por eso no cuentan para el progreso hacia 1.0.0. El
inventario de abajo es otra cosa: son incumplimientos de requerimientos **ya
congelados** (RF-5.1, RF-5.2, RF-6.2, RNF-6), y por eso sí se arreglan dentro
de v1.0, en la fase 2 de [docs/05-roadmap.md](05-roadmap.md).

No es una lista de gustos: son criterios verificables, cada uno con su
inventario de incumplimientos actuales. La revisión es manual, antes de
comitear cambios de front — ver [Cómo se verifica](#cómo-se-verifica).

## Criterios

| ID | Criterio |
| ---- | ---------- |
| C-1 | **Paridad teclado ↔ pantalla.** Toda acción disponible por teclado tiene un control visible equivalente, y los atajos se anuncian en la interfaz en vez de darse por sabidos. El teclado es un acelerador, nunca la única vía. |
| C-2 | **Misma acción, mismo nombre, mismo sitio.** Una acción que existe en dos pantallas se llama igual, se ve igual y ocupa la misma posición relativa. |
| C-3 | **La interfaz refleja lo que el sistema está haciendo.** Toda pantalla que dependa del motor o de la red distingue visualmente: inactiva, en cola, trabajando (con progreso si se conoce), terminada, vacía y con error. No basta un "analizando…" en letra pequeña. |
| C-4 | **Estados compartidos, no artesanales.** Carga, error y vacío se resuelven con `Spinner`, `ErrorBox` y `EmptyState` de `apps/web/src/components/Feedback.tsx`. Nada de frases sueltas en texto plano para lo mismo. |
| C-5 | **Un dato, una forma.** La evaluación, la clasificación de jugada y el nombre del motor se presentan igual en todas partes: mismo signo, misma unidad, mismo punto de vista (blancas) y mismo formateador (`lib/score.ts`). |
| C-6 | **Legible sin saber de ajedrez.** Todo número del motor va acompañado de etiqueta, leyenda o representación visual. `+0.35` solo, sin más, no comunica nada a quien no lee evaluaciones. |
| C-7 | **Accesibilidad mínima.** Foco visible, `aria-label` en los botones que son solo icono, y ningún significado transmitido únicamente por color. |

## Inventario de incoherencias (al 2026-09-07)

Revisado el 2026-09-07 tras la pasada de **cimientos compartidos** (componentes
`Button`, `Panel`, `BoardWithEvalBar`, `MoveNavigator`, recetas de clases en
`components/styles.ts`, `Feedback.tsx` con `SuccessBox`/`WarningBox`/
`ProgressBox` y formateadores nuevos en `lib/format.ts`). Esa pasada cerró once
filas y abrió cinco. Revisado otra vez el mismo día, tras el cambio de la
**posición de partida del visor** (el ply -1 sale del PGN y no de un FEN
estándar escrito en el archivo): abrió las filas 26, 27 y 37. Va en dos tablas,
una por ítem del roadmap; la numeración es continua entre ambas para que una
fila se pueda citar por su número. Dentro de cada tabla se agrupa por criterio
—salvo las dos últimas de la tabla A, que se añadieron después de esa
ordenación— y dentro de cada grupo va primero lo que más estorba a quien no
sabe leer evaluaciones. Las filas 26 a 34 de la tabla B corrieron dos números
para dejar sitio a las nuevas. Las líneas son las del estado del repositorio en
esa fecha.

### A · Ítem "coherencia de la interfaz entre pantallas"

| # | Incoherencia | Dónde | Criterio |
| --- | -------------- | ------- | ---------- |
| 1 | El tablero de análisis no tiene controles de navegación en pantalla: solo responde a ← y →, anunciadas en una frase al pie. El visor tiene ⏮ ◀ ▶ ⏭ y contador "jugada / total". El componente ya está sacado y listo para las dos pantallas (`MoveNavigator`); lo que falta es adoptarlo aquí. | `features/board/BoardPage.tsx:252-254` frente a `features/viewer/GameViewerPage.tsx:226-234` y `components/board/MoveNavigator.tsx` | C-1 |
| 2 | El visor acepta además `Home` y `End`; el tablero de análisis no, sin motivo. | `GameViewerPage.tsx:115-116` vs `BoardPage.tsx:163-182` | C-1, C-2 |
| 3 | El incumplimiento inverso del 1: el visor no anuncia ninguno de sus cuatro atajos, hay que descubrirlos probando. El tablero sí anuncia los suyos. | `GameViewerPage.tsx:109-126` | C-1 |
| 4 | Promover (▲) y borrar (✕) una variante solo existen al pasar el ratón (`hidden group-hover:inline-flex`): sin equivalente por teclado, sin `group-focus-within` que los revele al tabular y sin ninguna vía táctil. Al tabular se cae en un botón invisible. | `features/board/VariationTree.tsx:145-166` | C-1, C-7 |
| 5 | Previsualizar una línea del motor sobre el tablero funciona con ratón y con tabulador, pero no se anuncia: la frase de ayuda bajo el tablero solo menciona arrastrar y ← / →, y la única pista está en el `title` de cada jugada, que hay que descubrir señalando. | `BoardPage.tsx:252-254` frente a `features/board/EngineLines.tsx:50-73` | C-1 |
| 6 | "Analizar" sigue nombrando una acción que no analiza: en el listado es un enlace que solo abre el visor. El botón del visor ya dice con qué motor analiza ("Analizar con Stockfish"), así que el choque literal desapareció, pero el verbo sigue prometiendo en el listado algo que no hace. | `features/games/GamesPage.tsx:186` frente a `GameViewerPage.tsx:190-194` | C-2 |
| 7 | Las acciones de cabecera van en orden distinto en dos pantallas equivalentes: visor `[Girar tablero · motor · Analizar con…]`; tablero `[Partida propia · Apagar motor · Girar tablero · Copiar PGN]`. "Girar tablero" es la primera en una y la tercera en la otra. | `GameViewerPage.tsx:172-196` vs `BoardPage.tsx:206-233` | C-2 |
| 8 | Filtrar por jugador funciona de dos maneras: en Partidas se aplica al teclear; en Estadísticas hace falta enviar el formulario con un botón "Ver". | `GamesPage.tsx:76-82` vs `features/dashboard/DashboardPage.tsx:46-65` | C-2 |
| 9 | Dos verbos para destruir: "Eliminar" (tablero guardado) y "Borrar esta jugada y lo que sigue" escondido en el `title` de un ✕ (variante). Ninguna de las dos pide confirmación. | `features/board/BoardsPage.tsx:131-137`, `VariationTree.tsx:157-165` | C-2 |
| 10 | El tablero de análisis solo distingue dos estados del motor: un "analizando…" en letra pequeña en la cabecera del panel, y líneas. No hay "en cola", ni progreso, ni terminado explícito; y apagar el motor hace desaparecer el panel entero en vez de mostrarlo inactivo. `ProgressBox` ya existe para esto y aquí no se usa. | `EngineLines.tsx:26-38`, `BoardPage.tsx:258-265` | C-3 |
| 11 | `analysisQuery.isError` no se usa nunca: si el análisis de la posición falla, el panel muestra el vacío "Sin líneas para esta posición", indistinguible de que el motor no haya encontrado nada. | `BoardPage.tsx:90-95, 258-265` | C-3, C-4 |
| 12 | Si el autoguardado falla, la cabecera se queda en "Guardando…" para siempre —`saveState` no tiene caso de error— mientras un `ErrorBox` aparece debajo diciendo lo contrario. | `BoardPage.tsx:50, 61-64, 199-203, 236` | C-3 |
| 13 | Si falla la consulta de análisis previos, el error se traga y la pantalla afirma "Sin analizar", que es una conclusión distinta de "no se pudo consultar". | `GameViewerPage.tsx:52-55, 267-271` | C-3 |
| 14 | La casilla "Partida propia" llama a la API fuera de toda mutación, sin estado de envío ni `catch`: si falla, la casilla se queda como estaba y no se dice nada. | `BoardPage.tsx:206-218` | C-3 |
| 15 | "Copiar PGN" escribe en el portapapeles sin ninguna señal de que haya ocurrido, ni manejo de fallo: se pulsa y no pasa nada visible. Ahora que existe `SuccessBox`, no hay excusa de componente. | `BoardPage.tsx:227-232` | C-3 |
| 16 | "Sin cambios sin guardar" como estado de reposo: una doble negación para decir que está todo guardado. | `BoardPage.tsx:202` | C-3, C-6 |
| 17 | La invitación a analizar con el otro motor es un párrafo con la receta de `EmptyState` copiada a mano y encogida (`rounded border border-dashed border-slate-300 … dark:border-slate-700`), a pocas líneas del `EmptyState` de verdad. | `GameViewerPage.tsx:277-281` frente a `components/Feedback.tsx:127-133` | C-4 |
| 18 | Significado transmitido solo por color: la fase con más pérdida media se marca pintando su barra de rojo, sin etiqueta, sin orden y sin nota que lo diga. | `DashboardPage.tsx:213-214, 228-234` | C-7 |
| 19 | El enlace activo de la navegación repite a mano la receta del botón primario (`px-3 py-1.5 text-sm` + `bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900`) en vez de salir de `buttonClasses`. Es lo único que quedó fuera de la extracción del componente `Button`. | `components/Layout.tsx:30-34` frente a `components/styles.ts:20-32` | transversal |
| 20 | Queda una segunda receta de caja, la de borde sin fondo (`rounded border border-slate-200 dark:border-slate-800`), escrita a mano seis veces para tablas y gráficos, mientras las demás cajas son `Panel` y sí llevan fondo. El resultado es que tablas y gráficos flotan sobre el fondo de la página y las tarjetas no, sin que nada lo justifique. | `GamesPage.tsx:146`, `DashboardPage.tsx:96,128,164,218,241` frente a `components/styles.ts:43-44` | transversal |
| 21 | La receta del botón de jugada —el que se pulsa para ir a una posición— está copiada cuatro veces con tres variantes distintas de relleno y de marca de "actual". Es el control más repetido de la aplicación y no tiene componente. | `features/viewer/MoveList.tsx:48-50`, `GameViewerPage.tsx:339-345`, `VariationTree.tsx:136-141`, `EngineLines.tsx:62-64` | transversal |
| 22 | La insignia de clasificación (`rounded px-1 text-[10px] leading-4` + `style.className`) está copiada tres veces, con un tamaño de letra arbitrario fuera de la escala de Tailwind. | `MoveList.tsx:54`, `features/viewer/EngineComparison.tsx:90`, `GameViewerPage.tsx:364` | transversal |
| 23 | Paridad claro/oscuro rota en los tres gráficos: `contentStyle` solo fija el tamaño de letra, así que el tooltip de recharts conserva su `backgroundColor: '#fff'` por defecto sobre el tema oscuro, y las marcas de eje se quedan en el `#666` de fábrica. | `features/viewer/EvalChart.tsx:52-59`, `DashboardPage.tsx:139, 224-227` | transversal |
| 24 | Escala: el panel lateral mide `22rem` en el visor y `24rem` en el tablero; las listas navegables, `28rem` y `26rem` de alto. Mismo layout, cuatro valores arbitrarios distintos. | `GameViewerPage.tsx:216, 334`, `MoveList.tsx:16`, `BoardPage.tsx:238`, `VariationTree.tsx:32` | transversal |
| 25 | El título de página es `text-2xl` en las cuatro pantallas de listado y `text-xl` en las dos de detalle, sin que nada lo justifique. | `GamesPage.tsx:41`, `BoardsPage.tsx:56`, `DashboardPage.tsx:45`, `features/engines/EnginesPage.tsx:22` frente a `GameViewerPage.tsx:161`, `BoardPage.tsx:198` | transversal |
| 26 | Nada dice que una partida no empiece en la posición estándar. El visor ya dibuja la posición de partida real del PGN (`[SetUp "1"]` + `[FEN ...]`: odds chess, Chess960, partidas desde posición), pero la enseña sin etiquetarla: quien no sabe de ajedrez ve un tablero con piezas de menos o descolocadas y no puede distinguir la partida de un fallo de la aplicación. En el listado no se puede ni marcar, porque `GameSummary` no trae el PGN ni un campo de variante. | `GameViewerPage.tsx:158, 168-176`, `GamesPage.tsx` (falta el campo en la API) | C-6 |
| 27 | La numeración de jugadas del visor sigue asumiendo que el ply 0 es la primera de las blancas (`floor(ply / 2) + 1`), en los dos listados y en la comparación de motores. Desde el cambio de la posición de partida, el tablero de esas partidas ya es el suyo, pero los números no: una partida que arranca en la jugada 12 se lista desde "1.". El tablero de análisis sí lo resuelve, con `plyFromFen(root.fen)`; llevarlo al visor pide subir ese ayudante a `lib/` y pasar el ply inicial a tres componentes. | `MoveList.tsx:65-71`, `GameViewerPage.tsx:351`, `EngineComparison.tsx:44` frente a `features/board/tree.ts:179-185` | C-5, C-2 |

### B · Ítem "legibilidad del análisis del motor" (RF-5.2 / RF-6.2)

| # | Incoherencia | Dónde | Criterio |
| --- | -------------- | ------- | ---------- |
| 28 | `ClassificationStyle.color` existe y está documentado como el color de los puntos del gráfico de evaluación, pero el gráfico no lo usa: la curva es de un solo color y no marca dónde estuvieron los errores. | `lib/classification.ts:14-15` frente a `EvalChart.tsx` | C-5, C-6 |
| 29 | La columna de evaluación del panel del motor sigue sin encabezado ni leyenda: `+0.35`, `M3+`, sin decir qué mide ni en qué unidad. La barra de evaluación ya traduce la primera línea a porcentaje y cada flecha lleva su número encima, pero las líneas segunda y tercera del panel siguen siendo cifras desnudas. | `EngineLines.tsx:48` | C-6 |
| 30 | El tablero de análisis no dice qué motor firma la evaluación: `analyzePosition` se llama sin `engine` y el panel se titula solo "Motor". El visor sí tiene selector. | `BoardPage.tsx:90-95`, `EngineLines.tsx:27-31` | C-2, C-5, C-6 |
| 31 | "V/T/D" sin desarrollar como encabezado en dos tablas, y los tres números de debajo solo se distinguen entre sí por el color de fondo. | `DashboardPage.tsx:102, 170, 267-280` | C-6, C-7 |
| 32 | La clasificación de jugada solo se ve como símbolo (`?!`, `??`, `★`) con el nombre escondido en un `title`; la única leyenda visible es el resumen del lateral, que solo aparece con el análisis ya terminado. | `MoveList.tsx:44-55`, `GameViewerPage.tsx:305-308` | C-6 |
| 33 | "pts de diferencia" en la comparación de motores son puntos de probabilidad de victoria, pero se leen como puntos de material. Es además el último número del front formateado a mano (`toFixed(0)`), y no se pasa por `lib/format.ts` justamente porque no es un porcentaje sino una diferencia entre dos. | `EngineComparison.tsx:48` | C-5, C-6 |
| 34 | El eje Y del gráfico de evaluación va de 0 a 100 sin título ni leyenda: lo que mide solo se descubre pasando el ratón por encima. | `EvalChart.tsx:49` | C-6 |
| 35 | "profundidad 20 · MultiPV 3" al pie del panel de precisión, sin explicación, mientras que Motores sí acompaña MultiPV con "líneas a calcular". | `GameViewerPage.tsx:252-255` frente a `EnginesPage.tsx:122-129` | C-6 |
| 36 | En el panel del motor, la primera jugada de cada línea se juega al pulsarla y las siguientes no hacen nada al pulsarlas, solo previsualizan al señalarlas. Todas son botones con el mismo aspecto; la diferencia se transmite con un `opacity-70` y un `title`. | `EngineLines.tsx:50-73` | C-6, C-7 |
| 37 | "Jugada" cuenta dos cosas distintas en la misma pantalla: el gráfico de evaluación numera medias jugadas ("Jugada 41", en el eje y en el tooltip) y la lista de jugadas y la comparación de motores numeran jugadas enteras ("21."). Pinchar en el gráfico lleva a la posición correcta, pero el número que se lee por el camino no es el mismo. | `EvalChart.tsx:48, 54` frente a `MoveList.tsx:65-71` y `EngineComparison.tsx:44` | C-5, C-6 |

Las filas **1 a 27** son el trabajo que el roadmap recoge como "coherencia de la
interfaz entre pantallas"; las **28 a 37**, el ítem de legibilidad del análisis
del motor (RF-5.2 / RF-6.2). Ambos en la fase 2 de
[docs/05-roadmap.md](05-roadmap.md).

**Cerradas el 2026-09-07** por la pasada de cimientos compartidos, por si se
buscan en un commit anterior: "Girar" pasó a "Girar tablero" en el tablero de
análisis; la barra de evaluación ya no aparece y desaparece, porque
`BoardWithEvalBar` la dibuja siempre y en su estado inactivo cuando no hay
evaluación; el error de FEN/PGN de la creación de tableros dejó de ser un
párrafo rojo suelto; hay `SuccessBox` y `ProgressBox` compartidos donde había
tres formas distintas de decir "salió bien" y un recuadro de progreso hecho a
mano; el nombre del motor, los porcentajes, la precisión y el control de tiempo
pasan todos por `lib/format.ts`; y las recetas de botón y de tarjeta salieron a
`components/Button.tsx`, `components/Panel.tsx` y `components/styles.ts`, con
el bloque "barra de evaluación + tablero" extraído a
`components/board/BoardWithEvalBar.tsx`. La precisión dejó de ser un número
pelado, aunque la unidad que se le puso está en discusión: es la fila 19.

**Decidido el 2026-09-07, no es incoherencia.** Dos cosas que este inventario
llegó a listar y el autor resolvió por criterio, no por descuido:

- **La precisión se enseña con `%`** ("87.3 %") aunque no sea una proporción,
  sino el índice 0-100 de Lichess. Es la convención del dominio —Lichess y
  chess.com la muestran así— y es de donde viene el usuario de LUCIA.
- **Los controles de tiempo se quedan en inglés** ("Bullet", "Blitz", "Rapid",
  "Daily"). "Blitz" y "bullet" son préstamos de uso corriente en el ajedrez en
  español; traducir unos sí y otros no dejaba cuatro formas gramaticales
  distintas en la misma columna, y son los términos que el usuario ya ve en
  chess.com.

**Cerradas el 2026-09-06** con el trabajo de legibilidad del análisis: no había
barra de evaluación en ninguna pantalla; el tablero de análisis no dibujaba las
flechas del motor; los dos vacíos del panel lateral del tablero eran párrafos
sueltos en vez de `EmptyState`; y ningún botón de solo icono tenía nombre
accesible.

**El visor con una sola flecha no es una incoherencia**, aunque el tablero de
análisis dibuje varias: el análisis guardado solo persiste `best_move_uci` por
jugada (`AnalyzedMoveOut` en `packages/shared-types`), así que no hay
alternativas que dibujar. Persistirlas y usarlas en el visor es RF-10.1 /
RF-10.2, en la fase 2 del roadmap. Cuando eso exista, si el visor no adopta la
misma forma de flechas que el tablero, entonces sí será fila de inventario.

**Los números no se localizan a propósito.** `formatDate` usa el locale `es`,
pero los decimales van con punto (`+1.25`, `54.3 %`) porque la notación de
evaluación en ajedrez lo usa en todas partes; poner coma en los porcentajes y
punto en las evaluaciones sería peor que el punto en los dos.

## Cómo se verifica

Antes de comitear cualquier cambio que toque `apps/web`:

1. Recorrer los siete criterios contra las pantallas afectadas.
2. Si el cambio introduce una acción, un estado o un dato del motor que ya
   existe en otra pantalla, comprobar que se llama, se coloca y se formatea
   igual — o cambiar las dos a la vez.
3. Si aparece una incoherencia que no se arregla en el mismo commit, añadirla
   al inventario de arriba en vez de dejarla suelta.

Cuando el inventario quede vacío, este documento pasa a ser solo la lista de
criterios y el paso 3 deja de tener sentido.

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

## Inventario de incoherencias (al 2026-09-06)

Reconstruido de cero contra el código el 2026-09-06 y revisado ese mismo día
tras el trabajo de legibilidad del análisis del motor (flechas MultiPV, barra
de evaluación y previsualización de línea), que cerró cinco filas y abrió
seis. Va agrupado por criterio; dentro de cada grupo, primero lo que más
estorba a quien no sabe leer evaluaciones. Las líneas son las del estado del
repositorio en esa fecha.

| # | Incoherencia | Dónde | Criterio |
| --- | -------------- | ------- | ---------- |
| 1 | El tablero de análisis no tiene controles de navegación en pantalla: solo responde a ← y →, anunciadas en una frase al pie. El visor tiene ⏮ ◀ ▶ ⏭ y contador "jugada / total". | `features/board/BoardPage.tsx:257-260` vs `features/viewer/GameViewerPage.tsx:231-259` | C-1 |
| 2 | El visor acepta además `Home` y `End`; el tablero de análisis no, sin motivo. | `GameViewerPage.tsx:105-106` vs `BoardPage.tsx:153-172` | C-1, C-2 |
| 3 | El incumplimiento inverso del 1: el visor no anuncia ninguno de sus cuatro atajos, hay que descubrirlos probando. El tablero sí anuncia los suyos. | `GameViewerPage.tsx:99-116` | C-1 |
| 4 | Promover (▲) y borrar (✕) una variante solo existen al pasar el ratón (`hidden group-hover:inline-flex`): sin equivalente por teclado, sin `group-focus-within` que los revele al tabular y sin ninguna vía táctil. Al tabular se cae en un botón invisible. | `features/board/VariationTree.tsx:145-167` | C-1, C-7 |
| 5 | Previsualizar una línea del motor sobre el tablero funciona con ratón y con tabulador, pero no se anuncia: la frase de ayuda bajo el tablero solo menciona arrastrar y ← / →, y la única pista está en el `title` de cada jugada, que hay que descubrir señalando. | `BoardPage.tsx:257-260` frente a `features/board/EngineLines.tsx:60-70` | C-1 |
| 6 | La misma acción se llama distinto: "Girar tablero" en el visor, "Girar" en el tablero de análisis. | `GameViewerPage.tsx:166` vs `BoardPage.tsx:221` | C-2 |
| 7 | "Analizar" nombra dos acciones distintas: en el listado es un enlace que solo abre el visor; en el visor es el botón que lanza el motor. | `features/games/GamesPage.tsx:188` vs `GameViewerPage.tsx:177-188` | C-2 |
| 8 | Las acciones de cabecera van en orden distinto en dos pantallas equivalentes: visor `[Girar tablero · motor · Analizar]`; tablero `[Partida propia · Apagar motor · Girar · Copiar PGN]`. "Girar" es la primera en una y la tercera en la otra. | `GameViewerPage.tsx:160-189` vs `BoardPage.tsx:196-231` | C-2 |
| 9 | Filtrar por jugador funciona de dos maneras: en Partidas se aplica al teclear; en Estadísticas hace falta enviar el formulario con un botón "Ver". | `GamesPage.tsx:76-84` vs `features/dashboard/DashboardPage.tsx:43-65` | C-2 |
| 10 | Dos verbos para destruir: "Eliminar" (tablero guardado) y "Borrar esta jugada y lo que sigue" escondido en el `title` de un ✕ (variante). Ninguna de las dos pide confirmación. | `features/board/BoardsPage.tsx:130-136`, `VariationTree.tsx:156-166` | C-2 |
| 11 | El tablero de análisis solo distingue dos estados del motor: un "analizando…" en letra pequeña en la cabecera del panel, y líneas. No hay "en cola", ni progreso, ni terminado explícito; y apagar el motor hace desaparecer el panel entero en vez de mostrarlo inactivo. | `EngineLines.tsx:26-38`, `BoardPage.tsx:262-271` | C-3 |
| 12 | `analysisQuery.isError` no se usa nunca: si el análisis de la posición falla, el panel muestra el vacío "Sin líneas para esta posición", indistinguible de que el motor no haya encontrado nada. | `BoardPage.tsx:83-88, 262-271` | C-3, C-4 |
| 13 | Si el autoguardado falla, la cabecera se queda en "Guardando…" para siempre —`saveState` no tiene caso de error— mientras un `ErrorBox` aparece debajo diciendo lo contrario. | `BoardPage.tsx:43, 54-57, 189-193, 234` | C-3 |
| 14 | Si falla la consulta de análisis previos, el error se traga y la pantalla afirma "Sin analizar", que es una conclusión distinta de "no se pudo consultar". | `GameViewerPage.tsx:42-45, 292-296` | C-3 |
| 15 | La casilla "Partida propia" llama a la API fuera de toda mutación, sin estado de envío ni `catch`: si falla, la casilla se queda como estaba y no se dice nada. | `BoardPage.tsx:197-208` | C-3 |
| 16 | "Copiar PGN" escribe en el portapapeles sin ninguna señal de que haya ocurrido, ni manejo de fallo: se pulsa y no pasa nada visible. | `BoardPage.tsx:223-230` | C-3 |
| 17 | "Sin cambios sin guardar" como estado de reposo: una doble negación para decir que está todo guardado. | `BoardPage.tsx:192` | C-3, C-6 |
| 18 | La barra de evaluación aparece y desaparece en vez de mostrarse inactiva, y con dos condiciones distintas: el tablero la pinta con el motor encendido y el visor solo con el análisis terminado. El tablero se desplaza lateralmente al aparecer, y el estado "sin datos" que `EvalBar` sí sabe pintar (`opacity-40` y "—") no se ve nunca en el visor, ni siquiera mientras el análisis corre. | `BoardPage.tsx:241-248` vs `GameViewerPage.tsx:217-220`, `features/viewer/EvalBar.tsx:26` | C-2, C-3 |
| 19 | Error a mano y `ErrorBox` a dos líneas de distancia dentro del mismo formulario: el error de FEN/PGN es un `<p>` rojo, el de la mutación un `ErrorBox`. | `BoardsPage.tsx:89-90` | C-4 |
| 20 | Tres formas de decir que algo salió bien, y ningún componente compartido para ello: recuadro verde con borde (Partidas), texto verde suelto (Motores), texto gris en la cabecera (tablero). `components/Feedback.tsx` no tiene equivalente de éxito. | `GamesPage.tsx:68-73`, `features/engines/EnginesPage.tsx:156-158`, `BoardPage.tsx:189-193` | C-4 |
| 21 | Tampoco hay componente compartido de "trabajando, y esto es lo que lleva": el visor se lo hace a mano en un recuadro índigo con barra de progreso y reloj, y `Feedback.tsx` solo ofrece `Spinner`, que no admite progreso. Por eso el tablero de análisis no puede reutilizarlo (fila 11). | `GameViewerPage.tsx:197-213` frente a `components/Feedback.tsx:4-11` | C-3, C-4 |
| 22 | El nombre del motor aparece de tres formas: "Stockfish"/"Lc0" en el selector, `stockfish` en minúscula cruda en el botón y en el pie del panel de precisión, y capitalizado por CSS en Motores. No hay formateador compartido. | `GameViewerPage.tsx:174-175, 185-187, 279`, `EnginesPage.tsx:74` | C-5 |
| 23 | La precisión pasa por `formatAccuracy` en tres sitios y se formatea a mano con `.toFixed(1)` en un cuarto. | `DashboardPage.tsx:245` frente a `lib/format.ts:12-14` | C-5 |
| 24 | Los porcentajes se formatean a mano en cada sitio, y la misma magnitud con distinta precisión: `score_percent.toFixed(1)}%` tres veces, la probabilidad de victoria con `.toFixed(0)}%` en la comparación de motores y `.toFixed(1)}%` en el gráfico, y `Math.round` con espacio antes del signo en la barra de evaluación. `lib/format.ts` no tiene formateador de porcentaje. | `DashboardPage.tsx:89,116,189`, `features/viewer/EngineComparison.tsx:91`, `features/viewer/EvalChart.tsx:55`, `EvalBar.tsx:29` | C-5 |
| 25 | `time_class` se muestra crudo en minúscula en Partidas y en el visor, y capitalizado por CSS en Estadísticas. | `GamesPage.tsx:180`, `GameViewerPage.tsx:156`, `DashboardPage.tsx:110` | C-5 |
| 26 | `ClassificationStyle.color` existe y está documentado como el color de los puntos del gráfico de evaluación, pero el gráfico no lo usa: la curva es de un solo color y no marca dónde estuvieron los errores. | `lib/classification.ts:14-15` frente a `EvalChart.tsx` | C-5, C-6 |
| 27 | La columna de evaluación del panel del motor sigue sin encabezado ni leyenda: `+0.35`, `M3+`, sin decir qué mide ni en qué unidad. La barra de evaluación ya traduce la primera línea a porcentaje y cada flecha lleva su número encima, pero las líneas segunda y tercera del panel siguen siendo cifras desnudas. | `EngineLines.tsx:48` | C-6 |
| 28 | El tablero de análisis no dice qué motor firma la evaluación: `analysePosition` se llama sin `engine` y el panel se titula solo "Motor". El visor sí tiene selector. | `BoardPage.tsx:83-88`, `EngineLines.tsx:28` | C-2, C-5, C-6 |
| 29 | La precisión se muestra como número pelado, sin unidad ni escala, junto a porcentajes que sí llevan `%`: en la misma fila de tarjetas conviven "Puntuación 54.3%" y "Precisión media 87.3". | `lib/format.ts:12-14`, `DashboardPage.tsx:88-91`, `GameViewerPage.tsx:268-277` | C-6 |
| 30 | "V/T/D" sin desarrollar como encabezado en dos tablas, y los tres números de debajo solo se distinguen entre sí por el color de fondo. | `DashboardPage.tsx:102, 170, 266-279` | C-6, C-7 |
| 31 | La clasificación de jugada solo se ve como símbolo (`?!`, `??`, `★`) con el nombre escondido en un `title`; la única leyenda visible es el resumen del lateral, que solo aparece con el análisis ya terminado. | `features/viewer/MoveList.tsx:44-54`, `GameViewerPage.tsx:308-311` | C-6 |
| 32 | "pts de diferencia" en la comparación de motores son puntos de probabilidad de victoria, pero se leen como puntos de material. | `EngineComparison.tsx:46` | C-6 |
| 33 | El eje Y del gráfico de evaluación va de 0 a 100 sin título ni leyenda: lo que mide solo se descubre pasando el ratón por encima. | `EvalChart.tsx:48` | C-6 |
| 34 | "profundidad 20 · MultiPV 3" al pie del panel de precisión, sin explicación, mientras que Motores sí acompaña MultiPV con "líneas a calcular". | `GameViewerPage.tsx:279` frente a `EnginesPage.tsx:119-126` | C-6 |
| 35 | En el panel del motor, la primera jugada de cada línea se juega al pulsarla y las siguientes no hacen nada al pulsarlas, solo previsualizan al señalarlas. Todas son botones con el mismo aspecto; la diferencia se transmite con un `opacity-70` y un `title`. | `EngineLines.tsx:55-72` | C-6, C-7 |
| 36 | Significado transmitido solo por color: la fase con más pérdida media se marca pintando su barra de rojo, sin etiqueta, sin orden y sin nota que lo diga. | `DashboardPage.tsx:213-214, 228-232` | C-7 |
| 37 | La receta de botón está copiada a mano y no existe un componente `Button`: la variante secundaria aparece 4 veces, la primaria 5 y la pequeña 6. La coherencia se sostiene con copiar y pegar. | `GameViewerPage.tsx:164,181,369`, `BoardPage.tsx:212,219,227`, `GamesPage.tsx:60,186,207,221`, `BoardsPage.tsx:95,133`, `DashboardPage.tsx:61`, `EnginesPage.tsx:152`, `components/ThemeToggle.tsx:31` | transversal |
| 38 | Lo mismo con la receta de tarjeta/panel (`rounded border border-slate-200 bg-white dark:…`), repetida 11 veces sin componente compartido, y con la de aviso ámbar, dos veces en Motores. | 11 apariciones en 8 archivos; `EnginesPage.tsx:84,90` | transversal |
| 39 | Paridad claro/oscuro rota en los tres gráficos: `contentStyle` solo fija el tamaño de letra, así que el tooltip de recharts conserva su `backgroundColor: '#fff'` por defecto sobre el tema oscuro, y las marcas de eje se quedan en el `#666` de fábrica. | `EvalChart.tsx:51-58`, `DashboardPage.tsx:139, 224-227` | transversal |
| 40 | Escala: el panel lateral mide `22rem` en el visor y `24rem` en el tablero; las listas navegables, `28rem` y `26rem` de alto. Mismo layout, cuatro valores arbitrarios distintos. | `GameViewerPage.tsx:215,387`, `MoveList.tsx:15`, `BoardPage.tsx:236`, `VariationTree.tsx:32` | transversal |
| 41 | El título de página es `text-2xl` en las cuatro pantallas de listado y `text-xl` en las dos de detalle, sin que nada lo justifique. | `GamesPage.tsx:39`, `BoardsPage.tsx:54`, `DashboardPage.tsx:42`, `EnginesPage.tsx:19` frente a `GameViewerPage.tsx:150`, `BoardPage.tsx:188` | transversal |
| 42 | El bloque "barra de evaluación + tablero" está copiado literal en las dos pantallas que lo tienen, con el ancho máximo escrito a mano en las dos (`mx-auto flex w-full max-w-[36rem] gap-3` más el envoltorio `min-w-0 flex-1`). El primer cambio de ancho o de separación se hará en una sola de ellas. | `BoardPage.tsx:238-256` y `GameViewerPage.tsx:217-228` | transversal |

Las filas 1 a 25 y 36 a 42 son el trabajo que el roadmap recoge como
"coherencia de la interfaz entre pantallas"; las filas 26 a 35 las cubre el
ítem de legibilidad del análisis del motor (RF-5.2 / RF-6.2). Ambos en la
fase 2 de [docs/05-roadmap.md](05-roadmap.md).

**Cerradas el 2026-09-06** con el trabajo de legibilidad del análisis y con
esta revisión, por si se buscan en un commit anterior: no había barra de
evaluación en ninguna pantalla (hoy la hay en el visor y en el tablero); el
tablero de análisis no dibujaba las flechas del motor (hoy dibuja hasta tres,
etiquetadas); los dos vacíos del panel lateral del tablero eran párrafos
sueltos en vez de `EmptyState`; y ningún botón de solo icono tenía nombre
accesible (hoy lo tienen ⏮ ◀ ▶ ⏭ del visor y ▲ ✕ del árbol de variantes).

**El visor con una sola flecha no es una incoherencia**, aunque el tablero de
análisis dibuje varias: el análisis guardado solo persiste `best_move_uci` por
jugada (`AnalyzedMoveOut` en `packages/shared-types`), así que no hay
alternativas que dibujar. Persistirlas y usarlas en el visor es RF-10.1 /
RF-10.2, en la fase 2 del roadmap. Cuando eso exista, si el visor no adopta la
misma forma de flechas que el tablero, entonces sí será fila de inventario.

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

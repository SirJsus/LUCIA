# `components` — lo que comparten las pantallas

Aquí vive lo que usan dos o más features. Si algo solo lo usa una pantalla, su
sitio es esa pantalla; en cuanto lo usa la segunda, se sube aquí en vez de
copiarse. Es lo que sostiene RNF-11 (coherencia de interfaz): que la misma cosa
se vea y se llame igual en todas partes no depende de acordarse, sino de que
haya un único sitio donde está escrita.

| Archivo | Qué es |
| --- | --- |
| `Button.tsx` | Botón, con variantes `primary` (una por pantalla), `secondary` y `danger`, y tamaños `md`/`sm`. |
| `Panel.tsx` | Caja con borde, con cabecera opcional (título + un hueco a la derecha para el estado). Es la unidad de agrupación: tablas y gráficos van dentro de uno, igual que las tarjetas. |
| `DataTable.tsx` | Tabla de datos con su cabecera: todas las que hay (partidas, control de tiempo, aperturas, salidas de la teoría, tipos de error, tramos de reloj) salen de aquí. Las clases de fila y celda están en `styles.ts`, porque las escribe quien pinta cada fila. |
| `EngineSelect.tsx` | Con qué motor analizar, en las dos pantallas que lo eligen (visor y tablero de análisis). Los nombres salen de `formatEngineName`, no escritos a mano. |
| `FilterBar.tsx` | La barra de filtros bajo el título y los campos que van dentro (`FilterText`, `FilterSelect`): la usan Partidas —nueve filtros (RF-5.3)— y Estadísticas —uno—, y así el filtro por jugador se ve igual en las dos. Un campo puede ir deshabilitado con el motivo en `hint`. |
| `FieldLabel.tsx` | Un campo con su etiqueta encima y su ayuda debajo. La misma receta estaba escrita de dos formas para el mismo resultado, y la ayuda unas veces se enseñaba y otras se escondía en un `title`; ahora la usan la barra de filtros y los formularios de sincronizar, crear tablero y configurar motores. La etiqueta envuelve al control, así que no hacen falta `for`/`id`. |
| `RecordBadges.tsx` | Victorias, tablas y derrotas de un marcador, sobre `Badge`. Cada número lleva su letra: los tres se distinguían solo por el color de fondo, que no es una diferencia para quien no lo ve (criterio C-7). Está aquí desde que lo usan tres tablas —control de tiempo, apertura y salidas de la teoría—; acepta cualquier cosa con las tres cifras, porque el marcador de las salidas de teoría no es un `RecordSummary` de la API sino tres campos sueltos de la misma respuesta. |
| `Badge.tsx` | La forma de una etiqueta corta de color sobre un dato, con cinco tonos. Quien tenga paleta propia le pasa `className`. |
| `ClassificationBadge.tsx` | La clasificación de una jugada (`??`, `★`, `?!`), sobre `Badge`. El símbolo va acompañado siempre de su nombre para quien no lee notación y para los lectores de pantalla. |
| `GameSourceBadge.tsx` | De dónde vino una partida cuando no es de chess.com: "PGN importado" (RF-1.5) o "tablero propio" (RF-6.5), con el motivo del hueco en el `title`. Existe porque un PGN importado enseña "—" en los dos ratings, en el control de tiempo y en el ritmo —un archivo no trae esos datos— y cuatro columnas vacías sin una palabra se leen como un fallo (fila 67). Las de chess.com no llevan insignia: son la mayoría y marcarlas todas sería ruido. La usan el listado y el visor, y convive con `CustomPositionBadge`. |
| `CustomPositionBadge.tsx` | El aviso de que un PGN trae su propia posición de partida (odds chess, Chess960, partida empezada desde una posición): un tablero al que le faltan piezas se lee como un fallo de la aplicación si nadie lo dice. Lo usan el listado de partidas, el visor y el listado de tableros. |
| `WdlBar.tsx` | El reparto de gana / tablas / pierde que da el **motor** (RF-2.6), en una barra de tres tramos con el porcentaje de victoria al lado. No es lo mismo que `EvalBar` y por eso se ve distinto: aquella reparte el tablero entre dos bandos a partir de una fórmula sobre el centipeón, igual para cualquier motor, y esto son tres números que contesta el motor —el tramo de las tablas es justo lo que la fórmula no sabe decir—. Usa los blancos y negros de `EvalBar` para que los bandos se reconozcan entre las dos barras. La comparten la lista de líneas del motor y la comparación entre motores del visor. |
| `Feedback.tsx` | Los estados por los que pasa una pantalla: `Spinner`, `ProgressBox` (trabajando, con progreso o indeterminado), `ErrorBox`, `SuccessBox`, `WarningBox` y `EmptyState`. |
| `styles.ts` | Las recetas de clases sueltas para lo que no puede ser uno de los componentes de arriba —un `<form>`, un `<li>`, un `<Link>` del router que se ve como botón, un `<td>`— y las medidas que dos pantallas tienen que compartir: `buttonClasses`, `PANEL_CLASSES`, `FIELD_CLASSES`, `MOVE_LIST_HEIGHT_CLASS`, `BOARD_SIDEBAR_GRID_CLASS`, `BOARD_HINT_CLASSES`, `NAV_LINK_CLASSES`, `TABLE_ROW_CLASSES` y `TABLE_CELL_CLASSES`. |
| `Layout.tsx`, `ThemeToggle.tsx` | Marco de la aplicación y conmutador de tema (RF-5.6). `Layout` marca en la navegación la sección de la ruta actual, y también la de sus pantallas de detalle: el visor de una partida pertenece a Partidas aunque su ruta no sea `/`. |

## `board/` — las piezas de ajedrez

Las comparten el visor de partidas (`features/viewer`) y el tablero de análisis
(`features/board`), que son dos pantallas distintas sobre el mismo tablero.

| Archivo | Qué es |
| --- | --- |
| `Chessboard.tsx` | Envoltorio de **chessground**, cuya API es imperativa: se construye una vez con `useRef` y después solo se le pasan actualizaciones. Tiene un hueco `overlay` para lo que se dibuja encima del tablero, y es quien dice qué casilla hay bajo el puntero (`onSelectSquare`, `onHoverSquare`): lo calcula midiendo sobre el rectángulo del tablero, porque chessground no avisa de la selección cuando el tablero es de solo lectura ni tiene evento de hover. |
| `boardConfig.ts` | La configuración que se le da a chessground, y la traducción de líneas del motor a flechas (RF-5.2). Vive aparte porque tiene una trampa que conviene poder probar: ver su docstring. |
| `EvalBar.tsx` | Barra de evaluación en probabilidad de victoria, orientada como el tablero: el bando de abajo es el del usuario, **y con su color**. La cifra es siempre la de las blancas, y lo dice. |
| `BoardWithEvalBar.tsx` | Las dos anteriores juntas, que es como aparecen en las dos pantallas. |
| `MoveNavigator.tsx` | Los controles ⏮ ◀ ▶ ⏭ con el punto donde estás. |
| `MoveButton.tsx` | El botón que lleva a una posición al pulsarlo. Es el control más repetido de la aplicación: lista de jugadas, lista sin analizar, árbol de variantes y líneas del motor. |
| `EngineLineList.tsx` | Las líneas del motor: evaluación, su W/D/L (RF-2.6, con `WdlBar`, y solo si el motor la informa) y continuación propuesta. La usan el panel del motor en vivo (`features/board/EngineLines`) y las alternativas de una jugada en el visor (RF-10.2); es el mismo dato, así que se lee igual. Señalar la jugada n de una línea dibuja sus n primeras jugadas sobre el tablero. Con `onPlayLine`, pulsar lleva el tablero hasta ahí (lo que puede el tablero de análisis); sin él, pulsar solo dibuja (lo único que puede el visor de una partida terminada). `playedUci` marca la línea que empieza por la jugada que se jugó de verdad. |
| `useMoveNavigationKeys.ts` | Los atajos que acompañan a `MoveNavigator` (← → e `Inicio`/`Fin`). Escucha en `window` porque el foco no está en los botones, y por eso ignora las pulsaciones que son de un campo o de un desplegable (`lib/keyboard.ts::isTypingTarget`, la misma regla en todos los atajos). |
| `pieces.ts` | Lo que hace falta saber de cada clase de pieza: cómo la nombra chessground, cómo se llama en español —con su color ya concordado, "Torre negra"— y cuánto vale. La comparten la paleta del editor de posición (RF-6.1) y la capa de ocupación, que nombra atacantes y pesa piezas con la misma tabla. |
| `squares.ts` | La geometría del tablero: las 64 casillas y dónde cae cada una en pantalla según la orientación. La usan todas las capas que se superponen al tablero, para que el tinte, la línea y la casilla enfocable señalen la misma. |
| `SquareKeyboardGrid.tsx` | Las 64 casillas como botones enfocables encima del tablero, porque chessground no hace enfocable ninguna (criterio C-1). Va con `pointer-events-none`: solo aporta paradas de foco y la tecla Intro, y el ratón sigue llegando al tablero. Una sola parada de tabulador, flechas para moverse dentro. La usan el editor de posición (Intro coloca la pieza) y la capa de ocupación (Intro inspecciona la casilla); lo único que cambia es qué se lee de cada casilla (`describeSquare`). |
| `occupancy.ts` | Quién ataca y quién defiende cada casilla de una posición (RF-7.1 a RF-7.7): lógica pura, sin motor y sin API. Probada aparte en `__tests__/occupancy.test.ts`. |
| `useOccupancy.ts` | El estado de la capa —sub-modo, bando, marcas, casilla inspeccionada— y el atajo `O`. Un solo hook para las dos pantallas, que es lo que evita que la capa se comporte distinto en cada una (RNF-11). |
| `OccupancyLayer.tsx` | Lo que se pinta encima del tablero: los tintes con su número, los conectores en SVG —continuos los directos, discontinuos los rayos X (RF-7.5)— y la rejilla enfocable. Se le pasa a `Chessboard` por `overlay`. |
| `OccupancyPanel.tsx` | El control de la capa, la inspección de la casilla elegida (RF-7.3) y la leyenda de todo lo que se ve. Va **bajo** el tablero, no en el lateral: es la leyenda de lo que se está pintando sobre él. |

De dónde salen los números de la barra: en el visor, del análisis guardado
(`win_percent_after`, ya calculado por el backend); en el tablero de análisis,
de la evaluación en vivo, convertida en el cliente con
`lib/score.ts::whiteWinPercentFromScore` — ver
[ADR-0006](../../../../docs/adr/0006-probabilidad-de-victoria-en-el-cliente.md).

## La capa de ocupación (RF-7)

Entra el FEN de la posición que se está mirando —la jugada del visor o el nodo
del tablero de análisis— y sale el mapa de alcances; el visor y el tablero lo
pintan igual porque es el mismo hook y los mismos componentes. **No pasa por la
API ni por el motor** y no se guarda nada: se recalcula al cambiar de posición.
Recordar el sub-modo entre sesiones es RF-7.8 y las casillas críticas según
motor RF-7.9, los dos P2 y fuera de la v1.0.

Los alcances se generan a mano en vez de usar `attackers()` de chess.js, que
devuelve solo casillas de origen: hacen falta la pieza que ataca (para ordenar
la inspección por valor), el rayo X separado del ataque directo y la clavada de
los **dos** bandos, y chess.js solo calcula las jugadas legales del que tiene el
turno. A chess.js se le pide únicamente leer el FEN.

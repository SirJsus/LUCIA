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
| `CustomPositionBadge.tsx` | El aviso de que un PGN trae su propia posición de partida (odds chess, Chess960, partida empezada desde una posición): un tablero al que le faltan piezas se lee como un fallo de la aplicación si nadie lo dice. Lo usan el listado de partidas, el visor y el listado de tableros. |
| `Feedback.tsx` | Los estados por los que pasa una pantalla: `Spinner`, `ProgressBox` (trabajando, con progreso o indeterminado), `ErrorBox`, `SuccessBox`, `WarningBox` y `EmptyState`. |
| `styles.ts` | Las recetas de clases sueltas para lo que no puede ser uno de los componentes de arriba —un `<form>`, un `<li>`, un `<Link>` del router que se ve como botón, un `<td>`— y las medidas que dos pantallas tienen que compartir: `buttonClasses`, `PANEL_CLASSES`, `FIELD_CLASSES`, `MOVE_LIST_HEIGHT_CLASS`, `BOARD_SIDEBAR_GRID_CLASS`, `BOARD_HINT_CLASSES`, `TABLE_ROW_CLASSES` y `TABLE_CELL_CLASSES`. |
| `Layout.tsx`, `ThemeToggle.tsx` | Marco de la aplicación y conmutador de tema (RF-5.6). `Layout` marca en la navegación la sección de la ruta actual, y también la de sus pantallas de detalle: el visor de una partida pertenece a Partidas aunque su ruta no sea `/`. |

## `board/` — las piezas de ajedrez

Las comparten el visor de partidas (`features/viewer`) y el tablero de análisis
(`features/board`), que son dos pantallas distintas sobre el mismo tablero.

| Archivo | Qué es |
| --- | --- |
| `Chessboard.tsx` | Envoltorio de **chessground**, cuya API es imperativa: se construye una vez con `useRef` y después solo se le pasan actualizaciones. |
| `boardConfig.ts` | La configuración que se le da a chessground, y la traducción de líneas del motor a flechas (RF-5.2). Vive aparte porque tiene una trampa que conviene poder probar: ver su docstring. |
| `EvalBar.tsx` | Barra de evaluación en probabilidad de victoria, orientada como el tablero: el bando de abajo es el del usuario, **y con su color**. La cifra es siempre la de las blancas, y lo dice. |
| `BoardWithEvalBar.tsx` | Las dos anteriores juntas, que es como aparecen en las dos pantallas. |
| `MoveNavigator.tsx` | Los controles ⏮ ◀ ▶ ⏭ con el punto donde estás. |
| `MoveButton.tsx` | El botón que lleva a una posición al pulsarlo. Es el control más repetido de la aplicación: lista de jugadas, lista sin analizar, árbol de variantes y líneas del motor. |
| `EngineLineList.tsx` | Las líneas del motor: evaluación y continuación propuesta. La usan el panel del motor en vivo (`features/board/EngineLines`) y las alternativas de una jugada en el visor (RF-10.2); es el mismo dato, así que se lee igual. Señalar la jugada n de una línea dibuja sus n primeras jugadas sobre el tablero. Con `onPlayLine`, pulsar lleva el tablero hasta ahí (lo que puede el tablero de análisis); sin él, pulsar solo dibuja (lo único que puede el visor de una partida terminada). `playedUci` marca la línea que empieza por la jugada que se jugó de verdad. |
| `useMoveNavigationKeys.ts` | Los atajos que acompañan a `MoveNavigator` (← → e `Inicio`/`Fin`). Escucha en `window` porque el foco no está en los botones, y por eso ignora las pulsaciones que son de un campo o de un desplegable. |

De dónde salen los números de la barra: en el visor, del análisis guardado
(`win_percent_after`, ya calculado por el backend); en el tablero de análisis,
de la evaluación en vivo, convertida en el cliente con
`lib/score.ts::whiteWinPercentFromScore` — ver
[ADR-0006](../../../../docs/adr/0006-probabilidad-de-victoria-en-el-cliente.md).

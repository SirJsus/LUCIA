# `components` — lo que comparten las pantallas

Aquí vive lo que usan dos o más features. Si algo solo lo usa una pantalla, su
sitio es esa pantalla; en cuanto lo usa la segunda, se sube aquí en vez de
copiarse. Es lo que sostiene RNF-11 (coherencia de interfaz): que la misma cosa
se vea y se llame igual en todas partes no depende de acordarse, sino de que
haya un único sitio donde está escrita.

| Archivo | Qué es |
| --- | --- |
| `Button.tsx` | Botón, con variantes `primary` (una por pantalla), `secondary` y `danger`, y tamaños `md`/`sm`. |
| `Panel.tsx` | Caja con borde, con cabecera opcional (título + un hueco a la derecha para el estado). |
| `Feedback.tsx` | Los estados por los que pasa una pantalla: `Spinner`, `ProgressBox` (trabajando, con progreso o indeterminado), `ErrorBox`, `SuccessBox`, `WarningBox` y `EmptyState`. |
| `styles.ts` | Las recetas de clases sueltas (`buttonClasses`, `PANEL_CLASSES`, `FIELD_CLASSES`) para lo que no puede ser uno de los componentes de arriba: un `<form>`, un `<li>`, un `<Link>` del router que se ve como botón. |
| `Layout.tsx`, `ThemeToggle.tsx` | Marco de la aplicación y conmutador de tema (RF-5.6). |

## `board/` — las piezas de ajedrez

Las comparten el visor de partidas (`features/viewer`) y el tablero de análisis
(`features/board`), que son dos pantallas distintas sobre el mismo tablero.

| Archivo | Qué es |
| --- | --- |
| `Chessboard.tsx` | Envoltorio de **chessground**, cuya API es imperativa: se construye una vez con `useRef` y después solo se le pasan actualizaciones. |
| `boardConfig.ts` | La configuración que se le da a chessground, y la traducción de líneas del motor a flechas (RF-5.2). Vive aparte porque tiene una trampa que conviene poder probar: ver su docstring. |
| `EvalBar.tsx` | Barra de evaluación en probabilidad de victoria, orientada como el tablero. |
| `BoardWithEvalBar.tsx` | Las dos anteriores juntas, que es como aparecen en las dos pantallas. |
| `MoveNavigator.tsx` | Los controles ⏮ ◀ ▶ ⏭ con el punto donde estás. |

De dónde salen los números de la barra: en el visor, del análisis guardado
(`win_percent_after`, ya calculado por el backend); en el tablero de análisis,
de la evaluación en vivo, convertida en el cliente con
`lib/score.ts::whiteWinPercentFromScore` — ver
[ADR-0006](../../../../docs/adr/0006-probabilidad-de-victoria-en-el-cliente.md).

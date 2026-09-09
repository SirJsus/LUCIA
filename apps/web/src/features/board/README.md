# `features/board` — tablero de análisis

Las pantallas de RF-6: lista de tableros guardados (`BoardsPage`, RF-6.1 y
RF-6.4) y el tablero en sí (`BoardPage`, RF-6.2 a RF-6.5), donde se mueven
piezas a mano, se ramifican variantes y se consulta al motor en vivo con
autoguardado.

| Archivo | Qué es |
| --- | --- |
| `BoardsPage.tsx` | Lista y creación de tableros (posición inicial, FEN o PGN pegado). Se entra por el enlace "Ver tablero" del final de la fila, como en el listado de partidas |
| `BoardPage.tsx` | El tablero: jugadas, motor en vivo, teclado y autoguardado |
| `tree.ts` | El árbol de variantes (añadir, promover, borrar, exportar a PGN) y la validación de jugadas con chess.js |
| `VariationTree.tsx` | Navegación visual de ese árbol (RF-6.3) |
| `EngineLines.tsx` | Panel de líneas del motor (RF-6.2). Lo propio de aquí son los **estados** del motor —apagado, buscando, con error, sin líneas, con líneas—; las líneas las pinta `components/board/EngineLineList`, compartido con el visor: previsualiza la continuación al señalar una jugada y, al pulsarla, el tablero avanza hasta ahí |

Al motor se le pide la posición con 400 ms de retardo, para no lanzar una
petición por cada jugada de una secuencia rápida. Durante esa espera lo que hay
en pantalla es la evaluación de la posición **anterior**, así que el panel dice
que está analizando y la barra se queda sin cifra: callarlo hacía que la barra
afirmara lo contrario que el tablero mientras se avanzaba por una línea.

Lo visual del tablero no vive aquí: `Chessboard`, `EvalBar`,
`BoardWithEvalBar`, `MoveNavigator`, `MoveButton`, `EngineLineList` y
`boardConfig` están en `components/board/` y se comparten con el visor de
partidas para que las dos pantallas se vean y se lean igual (RNF-11). La lista
de líneas se subió ahí con RF-10.2, cuando el visor pasó a enseñar las mismas
alternativas que este tablero.

El servidor guarda el árbol como JSON opaco (`boards.tree_json`), así que las
reglas de ajedrez solo se aplican aquí; si el JSON llega con una forma
inesperada, `BoardPage` reconstruye desde el FEN raíz en vez de romper.

Un tablero no tiene por qué arrancar en la posición estándar (se crea desde
un FEN o desde un PGN con `[SetUp "1"]`), así que la numeración de las
jugadas se deriva de la posición raíz con `plyFromFen` (`lib/moves.ts`), y la
usan tanto `VariationTree` en pantalla como `toPgn` al exportar, para que la
misma jugada no salga con dos números distintos. Ese módulo es compartido: el
visor numera con él exactamente igual.

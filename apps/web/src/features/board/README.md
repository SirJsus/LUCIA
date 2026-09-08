# `features/board` — tablero de análisis

Las pantallas de RF-6: lista de tableros guardados (`BoardsPage`, RF-6.1 y
RF-6.4) y el tablero en sí (`BoardPage`, RF-6.2 a RF-6.5), donde se mueven
piezas a mano, se ramifican variantes y se consulta al motor en vivo con
autoguardado.

| Archivo | Qué es |
| --- | --- |
| `BoardsPage.tsx` | Lista y creación de tableros (posición inicial, FEN o PGN pegado) |
| `BoardPage.tsx` | El tablero: jugadas, motor en vivo, teclado y autoguardado |
| `tree.ts` | El árbol de variantes (añadir, promover, borrar, exportar a PGN) y la validación de jugadas con chess.js |
| `VariationTree.tsx` | Navegación visual de ese árbol (RF-6.3) |
| `EngineLines.tsx` | Panel de líneas del motor (RF-6.2), con previsualización de la continuación al señalarlas |

Lo visual del tablero no vive aquí: `Chessboard`, `EvalBar`,
`BoardWithEvalBar`, `MoveNavigator` y `boardConfig` están en
`components/board/` y se comparten con el visor de partidas para que las dos
pantallas se vean y se lean igual (RNF-11).

El servidor guarda el árbol como JSON opaco (`boards.tree_json`), así que las
reglas de ajedrez solo se aplican aquí; si el JSON llega con una forma
inesperada, `BoardPage` reconstruye desde el FEN raíz en vez de romper.

Un tablero no tiene por qué arrancar en la posición estándar (se crea desde
un FEN o desde un PGN con `[SetUp "1"]`), así que la numeración de las
jugadas se deriva de la posición raíz con `plyFromFen` (`tree.ts`), y la usan
tanto `VariationTree` en pantalla como `toPgn` al exportar, para que la misma
jugada no salga con dos números distintos.

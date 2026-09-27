# `features/board` — tablero de análisis

Las pantallas de RF-6: lista de tableros guardados y su creación
(`BoardsPage` con el `PositionEditor`, RF-6.1 y RF-6.4) y el tablero en sí
(`BoardPage`, RF-6.2 a RF-6.9), donde se mueven
piezas a mano, se ramifican variantes, se consulta al motor en vivo con
autoguardado, se importa y exporta PGN (RF-6.7), se deshace y rehace
(RF-6.8), se pide el análisis completo de la línea principal (RF-6.9) y se
marca el tablero como "partida propia" para que cuente en el historial y en
las estadísticas (RF-6.5).

| Archivo              | Qué es                                                                                                                                                                                                                                                                                                                      |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BoardsPage.tsx`     | Lista y creación de tableros (posición inicial, FEN, PGN pegado o el editor de posición). Se entra por el enlace "Ver tablero" del final de la fila, como en el listado de partidas                                                                                                                                         |
| `PositionEditor.tsx` | El editor de posición pieza a pieza (RF-6.1): tablero editable, paleta, turno, enroques y captura al paso. No crea el tablero, escribe el FEN montado en el campo "FEN o PGN" de `BoardsPage`                                                                                                                               |
| `position.ts`        | La posición que se está montando y su FEN (`toFen`/`fromFen`, `positionError`). Lógica pura, probada aparte                                                                                                                                                                                                                 |
| `BoardPage.tsx`      | El tablero: jugadas, motor en vivo, teclado, autoguardado, importar PGN, deshacer / rehacer, análisis completo y la marca de partida propia                                                                                                                                                                                 |
| `tree.ts`            | El árbol de variantes (añadir, promover, borrar, PGN en los dos sentidos con `toPgn`/`fromPgn`) y la validación de jugadas con chess.js; `matchAnalyzedLine` empareja un análisis con la línea principal de ahora                                                                                                           |
| `OwnGamePanel.tsx`   | Marcar el tablero como "partida propia" (RF-6.5): `OwnGameStatus` es la línea de la cabecera que dice si cuenta y abre el panel, y `OwnGamePanel` el formulario que publica o retira. Lo que se escribe aquí viaja a `PUT /boards/{id}/own-game` con el PGN del árbol y se convierte en una fila del historial              |
| `VariationTree.tsx`  | Navegación visual de ese árbol (RF-6.3), con la clasificación de cada jugada cuando hay análisis                                                                                                                                                                                                                            |
| `useUndoRedoKeys.ts` | Ctrl+Z / Ctrl+Y / Ctrl+Mayús+Z (RF-6.8). Aparte de `useMoveNavigationKeys` porque son teclas que solo existen en esta pantalla                                                                                                                                                                                              |
| `EngineLines.tsx`    | Panel de líneas del motor (RF-6.2). Lo propio de aquí son los **estados** del motor —apagado, buscando, con error, sin líneas, con líneas—; las líneas las pinta `components/board/EngineLineList`, compartido con el visor: previsualiza la continuación al señalar una jugada y, al pulsarla, el tablero avanza hasta ahí |

Al motor se le pide la posición con 400 ms de retardo, para no lanzar una
petición por cada jugada de una secuencia rápida. Durante esa espera lo que hay
en pantalla es la evaluación de la posición **anterior**, así que el panel dice
que está analizando y la barra se queda sin cifra: callarlo hacía que la barra
afirmara lo contrario que el tablero mientras se avanzaba por una línea.

Lo visual del tablero no vive aquí: `Chessboard`, `EvalBar`,
`BoardWithEvalBar`, `MoveNavigator`, `MoveButton`, `EngineLineList`,
`boardConfig` y la capa de ocupación (RF-7) están en `components/board/` y se comparten con el visor de
partidas para que las dos pantallas se vean y se lean igual (RNF-11). La lista
de líneas se subió ahí con RF-10.2, cuando el visor pasó a enseñar las mismas
alternativas que este tablero.

El servidor guarda el árbol como JSON opaco (`boards.tree_json`), así que las
reglas de ajedrez solo se aplican aquí; si el JSON llega con una forma
inesperada, `BoardPage` reconstruye desde el FEN raíz en vez de romper. Por lo
mismo, el PGN que se manda a analizar (RF-6.9) lo compone `toPgn` en el
cliente: la API no sabe recorrer el árbol.

**Deshacer no es una pila local** (RF-6.8): el historial está en la base
(`board_versions` y un cursor en `boards`, [ADR-0012](../../../../../docs/adr/0012-historial-de-tablero-lineal-y-persistido.md)),
así que sobrevive a recargar y el botón se habilita con el `can_undo`/`can_redo`
que trae el tablero. Antes de deshacer, de rehacer o de analizar se llama a
`flushPendingSave`: el autoguardado escribe con retardo y, sin eso, la petición
llegaría antes que la última jugada y se deshacía la equivocada.

El análisis del tablero es el mismo que el de una partida —mismo worker, mismo
WebSocket de progreso, `lib/useTrackedAnalysis`— y por eso puede quedarse
viejo: `matchAnalyzedLine` empareja lo analizado con la línea principal de
ahora mientras coincida y la pantalla avisa en cuanto deja de coincidir, en vez
de enseñar la clasificación de otra jugada. Un tablero analizado **no cuenta en
las estadísticas** ([ADR-0013](../../../../../docs/adr/0013-analisis-de-partida-o-de-tablero.md))
salvo que esté marcado como partida propia, que es la excepción de abajo.

**Marcar "partida propia" es un formulario, no una casilla** (RF-6.5,
[ADR-0014](../../../../../docs/adr/0014-tablero-propio-publicado-como-partida.md)).
Las estadísticas necesitan cuatro datos que un tablero no tiene —de qué color
jugó el usuario, contra quién, cómo acabó y qué día—, así que `OwnGamePanel`
los pide y `PUT /boards/{id}/own-game` publica el tablero como una fila más del
historial: a partir de ahí sale en Partidas y cuenta en el dashboard sin que
ninguna consulta sepa que salió de aquí. Rating y control de tiempo se quedan
en hueco, como en una partida importada de un PGN, y el panel lo dice antes de
pulsar. Consecuencias para esta pantalla:

- **Las jugadas viajan siempre en PGN** (`toPgn`), porque la API no recorre el
  árbol. Por eso `PUT /boards/{id}` manda también el `pgn` cuando el tablero
  está publicado: sin él la API responde 422 antes que dejar la partida del
  historial atrasada.
- **Deshacer y rehacer no republican nada desde aquí.** Cada versión del
  historial guarda su PGN (`board_versions.pgn`), así que `POST /boards/{id}/undo`
  y `/redo` ponen al día la partida publicada en esa misma petición y
  `BoardPage` solo tiene que pintar el tablero que le devuelven. La excepción
  son las versiones anteriores a esa columna, que no traen PGN: ahí el servidor
  desenlaza el análisis —deja de contar— hasta el siguiente guardado.
- **El análisis cuenta solo mientras siga siendo el de estas jugadas**: es la
  misma regla de `matchAnalyzedLine`, aplicada a lo que el dashboard suma, y la
  cabecera dice cuál de los dos casos es.

**El editor de posición no usa `Chess` de chess.js como modelo** (RF-6.1): a
medio montar, una posición es ilegal casi siempre —sin reyes, con tres damas—
y chess.js se niega a cargarla, así que `position.ts` guarda lo puesto sin
juzgarlo y llama a chess.js solo al final, para decir si sirve; a `validateFen`
se le suma una comprobación que él no hace, que el bando que no mueve no esté
dando jaque. La rejilla de 64 botones que `PositionEditor` superpone al
tablero existe porque chessground no hace enfocable ninguna casilla: va con
`pointer-events-none`, así que solo aporta paradas de foco y el ratón sigue
llegando al tablero de siempre. Esa rejilla ya no es de aquí: cuando la capa de
ocupación necesitó lo mismo pasó a ser `components/board/SquareKeyboardGrid`,
y los nombres y valores de las piezas, a `components/board/pieces.ts`.

**La capa de ocupación se enciende sobre este tablero** (RF-7.1 a RF-7.7), con
la tecla `O` o desde su panel, igual que en el visor: `BoardPage` solo le pasa
el FEN del nodo actual a `useOccupancy` y le pasa ese controlador a
`Chessboard` por su propiedad `occupancyController`, que es quien dibuja
`OccupancyLayer` encima —el hueco `overlay` queda para la rejilla enfocable del
editor de posición, que es lo otro que se pinta sobre este tablero—. La rejilla
enfocable de **este** tablero ya no es de la capa: la monta `Chessboard` siempre
que haya algo que elegir, porque una casilla tiene aquí dos trabajos —ser origen
o destino de una jugada e inspeccionarse con la capa encendida— y solo quien
conoce los dos puede darle a Intro uno sin superponer dos rejillas. Por eso este
tablero se juega también **con el teclado** (`KEYBOARD_MOVE_HINT`, en la frase
de atajos de abajo) y no solo arrastrando. Todo lo demás —el cálculo, los
sub-modos y la leyenda— es de `components/board/`, para
que las cinco pantallas con tablero la lean igual. Aquí las tres marcas
arrancan encendidas, como en el visor; en las tres pantallas de entrenamiento
arrancan apagadas (ver `features/training/README.md`).

Un tablero no tiene por qué arrancar en la posición estándar (se crea desde
un FEN o desde un PGN con `[SetUp "1"]`), así que la numeración de las
jugadas se deriva de la posición raíz con `plyFromFen` (`lib/moves.ts`), y la
usan tanto `VariationTree` en pantalla como `toPgn` al exportar, para que la
misma jugada no salga con dos números distintos. Ese módulo es compartido: el
visor numera con él exactamente igual.

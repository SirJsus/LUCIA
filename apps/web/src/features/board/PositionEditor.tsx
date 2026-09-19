/** Editor de posición pieza a pieza (lo que faltaba de RF-6.1).
 *
 * Es la cuarta forma de empezar un tablero, junto a la posición inicial, un
 * FEN y un PGN pegado. No guarda nada: monta una posición y devuelve su FEN
 * al campo de la pantalla de Tableros, que es quien crea el tablero. Así hay
 * una sola forma de crear —la de siempre— y esto es un ayudante que escribe
 * en ella, no una segunda puerta que mantener en paralelo.
 *
 * **Las piezas se ponen de tres maneras**, y las tres hacen falta: se elige
 * una en la paleta y se pulsan las casillas (lo único que funciona con el
 * dedo), se arrastra desde la paleta hasta el tablero (lo que espera quien
 * viene de lichess), o se hace todo con el teclado. Las ya puestas se
 * arrastran para recolocarlas y se sueltan fuera del tablero para quitarlas.
 *
 * Lo del teclado no lo da chessground, que no hace enfocable ninguna casilla:
 * lo añade `SquareKeyboardGrid`, la rejilla que también usa la capa de
 * ocupación (criterio C-1 de docs/07-coherencia-ui.md, fila 83).
 *
 * La posición se lleva en `position.ts`, que es lógica pura y está probada
 * aparte; aquí solo está la pantalla.
 */
import type { Color, Role } from "chessground/types";
import { createElement, useCallback, useRef, useState } from "react";
import { Button } from "../../components/Button";
import { Chessboard, type ChessboardApi } from "../../components/board/Chessboard";
import {
  chessgroundColor,
  chessgroundRole,
  pieceName,
  type PieceColor,
  type PieceRole,
} from "../../components/board/pieces";
import { SquareKeyboardGrid } from "../../components/board/SquareKeyboardGrid";
import { FieldLabel } from "../../components/FieldLabel";
import { WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { BOARD_HINT_CLASSES, FIELD_CLASSES } from "../../components/styles";
import {
  CASTLING_FLAGS,
  EMPTY_POSITION,
  enPassantSquares,
  fromFen,
  positionError,
  STANDARD_STARTING_FEN,
  toFen,
  type CastlingFlag,
  type EditablePosition,
  type PieceCode,
} from "./position";

/** Las piezas de la paleta, en dos filas: las blancas debajo y las negras
 * encima, como se ven sentado al tablero. Dentro de cada fila, del peón al
 * rey, que es el orden en que se nombran. */
const PALETTE_ROWS: PieceCode[][] = [
  ["p", "n", "b", "r", "q", "k"],
  ["P", "N", "B", "R", "Q", "K"],
];

/** Lo que hace falta saber de una letra del FEN: el color lo dice la caja de
 * la letra y el resto sale de la tabla de piezas compartida, la misma que usa
 * la capa de ocupación para nombrarlas (criterio C-5). */
function describePiece(piece: PieceCode): { role: Role; color: Color; name: string } {
  const role = piece.toLowerCase() as PieceRole;
  const color: PieceColor = piece === piece.toUpperCase() ? "w" : "b";
  return {
    role: chessgroundRole(role),
    color: chessgroundColor(color),
    name: pieceName(role, color),
  };
}

/** Lo que se está poniendo al pulsar una casilla: una pieza, o la goma. */
type Brush = PieceCode | "erase";

/** La forma de los botones de la paleta: las doce piezas y la goma se eligen
 * igual, así que se ven igual. */
const PALETTE_BUTTON_CLASSES = "size-9 rounded border";

/** Cómo se marca el que está elegido. Con borde **y** fondo, no solo con
 * fondo: el color por sí solo no vale como única señal (criterio C-7). */
function selectedClasses(isSelected: boolean): string {
  return isSelected
    ? "border-indigo-500 bg-indigo-100 dark:bg-indigo-900/60"
    : "border-transparent hover:bg-slate-200 dark:hover:bg-slate-700";
}

export function PositionEditor({
  initialFen,
  onUse,
}: {
  /** De dónde parte el editor: lo que hubiera en el campo de la pantalla. */
  initialFen: string;
  /** El FEN montado, cuando se acepta. */
  onUse: (fen: string) => void;
}) {
  const [position, setPosition] = useState<EditablePosition>(
    () => fromFen(initialFen) ?? EMPTY_POSITION,
  );
  const [brush, setBrush] = useState<Brush>("P");
  const boardApi = useRef<ChessboardApi | null>(null);

  const fen = toFen(position);
  const error = positionError(fen);

  /** Relee el tablero después de arrastrar, quitar o soltar una pieza.
   *
   * Se lee el tablero entero en vez de seguir cada evento por separado:
   * chessground avisa del cambio por tres vías distintas (mover, soltar
   * fuera, pieza nueva) y reconstruir la posición a partir de las tres sería
   * tres formas de equivocarse. `getFen` devuelve solo la parte de las
   * piezas, que es justo lo que el arrastre puede haber cambiado.
   */
  const readBoard = useCallback(() => {
    const placement = boardApi.current?.getFen();
    if (!placement) return;
    const read = fromFen(`${placement} w - - 0 1`);
    if (read) setPosition((current) => ({ ...current, pieces: read.pieces }));
  }, []);

  const paintSquare = useCallback(
    (square: string) => {
      setPosition((current) => {
        const pieces = { ...current.pieces };
        if (brush === "erase") delete pieces[square];
        else pieces[square] = brush;
        return { ...current, pieces };
      });
    },
    [brush],
  );

  function update(changes: Partial<EditablePosition>) {
    setPosition((current) => ({ ...current, ...changes }));
  }

  function toggleCastling(flag: CastlingFlag) {
    const flags = new Set(position.castling);
    if (flags.has(flag)) flags.delete(flag);
    else flags.add(flag);
    // En el orden del estándar, no en el que se hayan pulsado: "kqKQ"
    // describe lo mismo que "KQkq" y no es un FEN válido.
    update({ castling: CASTLING_FLAGS.filter((each) => flags.has(each)).join("") });
  }

  return (
    <Panel bodyClassName="space-y-3 p-3">
      {/* `items-start`: sin él la columna del tablero se estira hasta la
          altura de la otra, y como `.cg-wrap` mide el 100% de su contenedor
          (index.css), el tablero salía rectangular y se comía el texto de
          debajo. */}
      <div className="grid items-start gap-4 sm:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <div className="space-y-2">
          <Chessboard
            fen={fen}
            editable
            onReady={(api) => (boardApi.current = api)}
            onPositionChange={readBoard}
            onSelectSquare={paintSquare}
            overlay={
              <SquareKeyboardGrid
                orientation="white"
                describeSquare={(square) => {
                  const piece = position.pieces[square];
                  return `${square}: ${piece ? describePiece(piece).name : "vacía"}`;
                }}
                onActivate={paintSquare}
              />
            }
          />
          <p className={BOARD_HINT_CLASSES}>
            Elige una pieza y pulsa las casillas, o arrástrala desde la paleta. Arrastra fuera del
            tablero para quitar una pieza. Con teclado: tabula hasta el tablero, muévete con las
            flechas y pon la pieza elegida con Intro.
          </p>
        </div>

        <div className="space-y-3">
          <fieldset>
            <legend className="opacity-70">Qué se coloca</legend>
            <div className="mt-1 space-y-1">
              {PALETTE_ROWS.map((row) => (
                <div key={row[0]} className="flex gap-1">
                  {row.map((piece) => (
                    <PaletteButton
                      key={piece}
                      piece={piece}
                      isSelected={brush === piece}
                      onSelect={() => setBrush(piece)}
                      onStartDrag={(event) => {
                        const { role, color } = describePiece(piece);
                        boardApi.current?.dragNewPiece({ role, color }, event);
                      }}
                    />
                  ))}
                </div>
              ))}
              {/* Se elige igual que una pieza —mismo tamaño, mismo borde al
                  estar elegida— y no con `variant="primary"`, que en esta
                  pantalla es de "Usar esta posición": dos formas de decir
                  "esto está elegido" en la misma paleta se leen como dos
                  cosas distintas (criterio C-2). */}
              <button
                type="button"
                onClick={() => setBrush("erase")}
                aria-pressed={brush === "erase"}
                aria-label="Goma: deja vacía la casilla que pulses"
                className={`${PALETTE_BUTTON_CLASSES} ${selectedClasses(brush === "erase")}`}
              >
                <span aria-hidden="true" className="text-lg">
                  ⌫
                </span>
              </button>
              {/* Qué hace la goma, a la vista y no en un `title`: con teclado
                  un `title` no aparece nunca (criterio C-6, la misma razón por
                  la que las ayudas de los filtros bajaron bajo su campo). */}
              <p className="text-xs opacity-60">
                La goma deja vacía la casilla que pulses.
              </p>
            </div>
          </fieldset>

          <FieldLabel label="Mueven">
            <select
              value={position.turn}
              onChange={(event) => update({ turn: event.target.value as "w" | "b" })}
              className={FIELD_CLASSES}
            >
              <option value="w">Blancas</option>
              <option value="b">Negras</option>
            </select>
          </FieldLabel>

          <fieldset>
            <legend className="opacity-70">Enroques disponibles</legend>
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm">
              {CASTLING_FLAGS.map((flag) => (
                <label key={flag} className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={position.castling.includes(flag)}
                    onChange={() => toggleCastling(flag)}
                  />
                  {CASTLING_LABELS[flag]}
                </label>
              ))}
            </div>
          </fieldset>

          <FieldLabel
            label="Captura al paso"
            hint="La casilla que acaba de saltar un peón, si el rival puede capturarlo ahí."
          >
            <select
              value={position.enPassant ?? ""}
              onChange={(event) => update({ enPassant: event.target.value || null })}
              className={FIELD_CLASSES}
            >
              <option value="">Ninguna</option>
              {enPassantSquares(position.turn).map((square) => (
                <option key={square} value={square}>
                  {square}
                </option>
              ))}
            </select>
          </FieldLabel>

          <div className="flex flex-wrap gap-2">
            <Button onClick={() => setPosition(fromFen(STANDARD_STARTING_FEN) ?? EMPTY_POSITION)}>
              Posición estándar
            </Button>
            <Button onClick={() => setPosition(EMPTY_POSITION)}>Vaciar tablero</Button>
          </div>
        </div>
      </div>

      {/* El FEN se enseña, no se esconde: es lo que va a guardarse, y quien
          ya sabe leerlo comprueba de un vistazo que es lo que quería. */}
      <p className="text-xs opacity-60">
        FEN de esta posición: <span className="font-mono break-all">{fen}</span>
      </p>

      {/* Qué falta para que la posición sirva, antes de pulsar y no después:
          el botón deshabilitado sin motivo visible es la fila 56 otra vez
          (criterio C-3). */}
      {error && <WarningBox>{error}</WarningBox>}

      {/* Solo "Usar esta posición": cerrar sin usar es el botón de arriba,
          que ya dice "Cancelar" mientras el panel está abierto. Es el patrón
          del panel de "Importar PGN" del tablero de análisis, y dos controles
          con dos nombres para cerrar lo mismo era la fila 84 (criterio C-2). */}
      <Button variant="primary" onClick={() => onUse(fen)} disabled={error !== null}>
        Usar esta posición
      </Button>
    </Panel>
  );
}

/** Los cuatro enroques como se nombran en español; la letra del FEN sola no
 * dice de quién es ni a qué lado (criterio C-6). */
const CASTLING_LABELS: Record<CastlingFlag, string> = {
  K: "Blancas, corto",
  Q: "Blancas, largo",
  k: "Negras, corto",
  q: "Negras, largo",
};

/** Una pieza de la paleta: se pulsa para elegirla y se arrastra para soltarla
 * directamente en una casilla. Es un `button` de verdad, así que se llega con
 * tabulador y se activa con Intro. */
function PaletteButton({
  piece,
  isSelected,
  onSelect,
  onStartDrag,
}: {
  piece: PieceCode;
  isSelected: boolean;
  onSelect: () => void;
  onStartDrag: (event: MouseEvent | TouchEvent) => void;
}) {
  const { role, color, name } = describePiece(piece);

  return (
    <button
      type="button"
      onClick={onSelect}
      // El arrastre empieza aquí y lo continúa chessground, que ya sabe
      // seguir el puntero hasta soltar. Elegir la pieza además de arrastrarla
      // deja el pincel donde el usuario lo tenía en la cabeza.
      onMouseDown={(event) => {
        onSelect();
        onStartDrag(event.nativeEvent);
      }}
      onTouchStart={(event) => {
        onSelect();
        onStartDrag(event.nativeEvent);
      }}
      aria-pressed={isSelected}
      aria-label={name}
      title={name}
      className={`${PALETTE_BUTTON_CLASSES} ${selectedClasses(isSelected)}`}
    >
      {/* `piece` es el elemento propio de chessground, no una etiqueta de
          HTML: se usa su clase para heredar la imagen y que la paleta enseñe
          exactamente lo que se verá en el tablero. Se crea con
          `createElement` porque TypeScript no conoce ese elemento y
          declararlo en el JSX global por un solo uso sería peor. */}
      {/* `cg-wrap` hace falta de verdad: los selectores de la hoja de
          piezas de chessground son `.cg-wrap piece.pawn.white`, así que sin
          ese ancestro el botón sale vacío. `piece-palette` deshace después su
          colocación dentro del tablero (ver index.css). */}
      <span className="cg-wrap piece-palette block size-full">
        {createElement("piece", { className: `${role} ${color}` })}
      </span>
    </button>
  );
}

/** Envoltorio de React sobre chessground (el tablero de lichess, GPL-3.0).
 *
 * Chessground tiene una API imperativa y maneja su propio DOM, así que se
 * crea una sola vez con `useRef` y después solo se le pasan actualizaciones
 * con `set()`. Volver a construirlo en cada render rompería las animaciones
 * y perdería el estado de arrastre.
 *
 * La configuración se arma en `buildBoardConfig`, aparte, porque hay que
 * tener cuidado con las claves `undefined` (ver su docstring).
 *
 * **Qué casilla está debajo del puntero se calcula aquí, con geometría**, y no
 * se le pregunta a chessground. Sus eventos de selección solo existen cuando
 * el tablero es manipulable, y el visor de partidas lo tiene en modo lectura;
 * además no hay evento alguno para "el ratón pasa por encima", que es lo que
 * necesita el sub-modo de cobertura de RF-7.2. Midiendo sobre el rectángulo
 * del tablero responden igual las cinco pantallas con tablero, y como los
 * manejadores van en el contenedor —que recibe los eventos que suben desde el
 * tablero— chessground sigue recibiendo el ratón intacto para arrastrar piezas.
 */
import { Chessground } from "chessground";
import type { Api } from "chessground/api";
import { useEffect, useRef, type ReactNode } from "react";
import { buildBoardConfig, type EngineArrow } from "./boardConfig";
import { OccupancyLayer } from "./OccupancyLayer";
import { describeSquareOccupancy, readPiecesFromFen } from "./occupancy";
import { pieceName } from "./pieces";
import { SquareKeyboardGrid } from "./SquareKeyboardGrid";
import { squaresInReadingOrder } from "./squares";
import type { OccupancyController } from "./useOccupancy";

export type { Api as ChessboardApi };

export interface ChessboardProps {
  fen: string;
  /** Flechas del motor sobre el tablero: sus mejores líneas, o la
   * continuación que se está previsualizando. Memorízalas en quien llama
   * (`useMemo`): si llegan recreadas en cada render, el tablero se
   * reconfigura en cada render. */
  engineArrows?: EngineArrow[];
  /** Última jugada jugada, para resaltar las dos casillas. */
  lastMoveUci?: string | null;
  orientation?: "white" | "black";
  /** Jugadas legales por casilla de origen. Si se pasa, el tablero deja
   * arrastrar piezas; si no, es de solo lectura (el visor de partidas). */
  legalMoves?: Map<string, string[]>;
  /** Turno al que se le permite mover; solo aplica con `legalMoves`. */
  turnColor?: "white" | "black";
  onMove?: (from: string, to: string) => void;
  /** Modo editor de posición (RF-6.1): las piezas se arrastran a cualquier
   * casilla sin comprobar reglas, y soltarlas fuera del tablero las quita.
   * Es lo contrario de `legalMoves`, así que no se usan juntos. */
  editable?: boolean;
  /** Cualquier cambio de piezas en modo editor, ya sea moviendo, quitando o
   * soltando una pieza nueva. Llega sin decir qué cambió: quien edita relee
   * el tablero entero con `getFen()` de la API, que es más simple que
   * reconstruirlo a partir de tres eventos distintos. */
  onPositionChange?: () => void;
  /** El controlador de la capa de ocupación de la pantalla (RF-7), si la
   * tiene —no el `OccupancyMap`, que es lo que ese controlador calcula—. Se
   * pasa entero y no sus piezas sueltas porque siempre van juntas —lo que se
   * dibuja encima, la casilla que se fija y la que se señala— y la capa se
   * orienta como el tablero: enchufarlas a mano era repetir tres líneas en
   * cada una de las cinco pantallas con tablero y poder equivocarse en una. */
  occupancyController?: OccupancyController;
  /** Al pulsar una casilla: así se coloca una pieza sin arrastrarla en el
   * editor (RF-6.1). Un arrastre no cuenta como pulsación —se suelta en otra
   * casilla—, que es lo que distingue colocar de mover. Sin esto manda
   * `occupancyController`, que usa la pulsación para elegir qué casilla
   * inspecciona (RF-7.3); un tablero no es editor y capa de ocupación a la
   * vez. */
  onSelectSquare?: (square: string) => void;
  /** Casilla sobre la que está el ratón, o `null` al salir del tablero. Como
   * `onSelectSquare`, sin esto manda `occupancyController`: la cobertura de
   * una pieza se filtra al señalarla (RF-7.2). */
  onHoverSquare?: (square: string | null) => void;
  /** Lo que se dibuja **encima** del tablero, ocupándolo entero: la rejilla de
   * casillas enfocables del editor. Va aquí y no en quien llama para que todas
   * las capas se coloquen igual sobre el mismo cuadrado. */
  overlay?: ReactNode;
  /** Recibe la API imperativa de chessground al montarse. Hace falta para lo
   * que no cabe en propiedades: soltar una pieza arrastrada desde la bandeja
   * (`dragNewPiece`) y releer las piezas (`getFen`). */
  onReady?: (api: Api) => void;
}

export function Chessboard({
  fen,
  engineArrows,
  lastMoveUci,
  orientation = "white",
  legalMoves,
  turnColor,
  onMove,
  editable = false,
  onPositionChange,
  occupancyController,
  onSelectSquare = occupancyController?.selectSquare,
  onHoverSquare = occupancyController?.hoverSquare,
  overlay,
  onReady,
}: ChessboardProps) {
  const boardRef = useRef<HTMLDivElement>(null);
  const apiRef = useRef<Api | null>(null);
  // Dónde empezó la pulsación, para distinguirla de un arrastre: si se suelta
  // en otra casilla, el usuario estaba moviendo una pieza, no eligiendo.
  const pressedSquare = useRef<string | null>(null);
  // La última casilla señalada, para avisar solo cuando cambia: el puntero
  // dispara decenas de eventos al cruzar una casilla y quien escucha lo
  // guardaría en un estado, redibujando la pantalla en cada uno.
  const hoveredSquare = useRef<string | null>(null);
  // Los callbacks se guardan en una ref porque chessground se configura una
  // sola vez: sin esto, los handlers quedarían congelados en los del primer
  // render. Se reasigna en cada render para que apunten siempre a los últimos.
  const handlers = useRef({ onMove, onPositionChange });
  handlers.current = { onMove, onPositionChange };

  useEffect(() => {
    if (!boardRef.current) return;
    apiRef.current = Chessground(boardRef.current, {
      ...buildBoardConfig({ fen, orientation, engineArrows, lastMoveUci, legalMoves, turnColor }),
      viewOnly: !editable && !handlers.current.onMove,
      coordinates: true,
      // Sin animación al editar: las piezas no se mueven, aparecen y
      // desaparecen, y animarlo las hace deslizarse por el tablero.
      animation: { enabled: !editable, duration: 150 },
      movable: editable
        ? { free: true, color: "both", events: {} }
        : {
            free: false,
            color: turnColor,
            dests: legalMoves as never,
            events: { after: (from, to) => handlers.current.onMove?.(from, to) },
          },
      // Soltar una pieza fuera del tablero la quita, que es como se borra sin
      // tener que elegir la goma en la paleta.
      draggable: { enabled: true, deleteOnDropOff: editable },
      events: { change: () => handlers.current.onPositionChange?.() },
    });
    onReady?.(apiRef.current);
    return () => {
      apiRef.current?.destroy();
      apiRef.current = null;
    };
    // Se monta una sola vez a propósito: el resto de cambios van por `set()`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    apiRef.current?.set(
      buildBoardConfig({ fen, orientation, engineArrows, lastMoveUci, legalMoves, turnColor }),
    );
    // Sin `legalMoves` el tablero deja de aceptar jugadas, y eso hay que
    // decírselo aparte: `buildBoardConfig` omite `movable` cuando no las hay
    // —mandarlo en `undefined` le borraría a chessground ese trozo de estado,
    // ver su docstring— y chessground conserva entonces los destinos de la
    // posición anterior. Sin esto, las piezas se seguían arrastrando sobre el
    // puzzle ya cerrado o sobre la jugada errónea que espera «Volver a
    // intentarlo», y el tablero quedaba enseñando una posición que no era la
    // de nadie (criterio C-3). El editor de posición no entra: mueve con
    // `movable.free` y no con destinos.
    if (!editable && !legalMoves) apiRef.current?.set({ movable: { dests: new Map() } });
  }, [fen, orientation, engineArrows, lastMoveUci, legalMoves, turnColor, editable]);

  function squareUnderPointer(event: { clientX: number; clientY: number }): string | null {
    const bounds = boardRef.current?.getBoundingClientRect();
    return bounds ? squareFromPoint(bounds, event.clientX, event.clientY, orientation) : null;
  }

  function reportHoveredSquare(square: string | null) {
    if (square === hoveredSquare.current) return;
    hoveredSquare.current = square;
    onHoverSquare?.(square);
  }

  /** Pulsar una casilla, venga del ratón o del teclado: es una sola cosa y hace
   * lo mismo por las dos vías. Para chessground es elegir —la primera pulsación
   * toma el origen y la segunda mueve, que es su propio `selectSquare`— y para
   * quien escucha, la casilla elegida (la capa de ocupación la inspecciona). */
  function activateSquare(square: string) {
    apiRef.current?.selectSquare(square as never);
    onSelectSquare?.(square);
  }

  return (
    <div
      className="relative aspect-square w-full"
      onPointerDown={(event) => (pressedSquare.current = squareUnderPointer(event))}
      onPointerUp={(event) => {
        // El ratón no pasa por `activateSquare`: chessground recibe el puntero
        // intacto y ya elige por su cuenta. Repetírselo desharía la selección
        // que él acaba de hacer.
        const releasedSquare = squareUnderPointer(event);
        if (releasedSquare && releasedSquare === pressedSquare.current)
          onSelectSquare?.(releasedSquare);
      }}
      onPointerMove={(event) => reportHoveredSquare(squareUnderPointer(event))}
      onPointerLeave={() => reportHoveredSquare(null)}
    >
      <div ref={boardRef} className="size-full" />
      {occupancyController && (
        <OccupancyLayer controller={occupancyController} orientation={orientation} />
      )}
      {/* La rejilla enfocable, una sola y para los dos trabajos que tiene una
          casilla: elegirla como origen o destino de una jugada y elegirla para
          inspeccionarla. Sin ella, los tableros donde se mueve una pieza solo
          se podían usar con el ratón —la única vía era arrastrar—, y la capa de
          ocupación traía la suya aparte (fila 91 del inventario de
          docs/07-coherencia-ui.md, criterio C-1). El editor de posición
          (RF-6.1) trae la suya por `overlay` y no es movible ni lleva capa, así
          que no salen dos. */}
      {(legalMoves !== undefined || occupancyController?.isActive) && (
        <SquareKeyboardGrid
          orientation={orientation}
          describeSquare={(square) => describeBoardSquare(fen, square, occupancyController)}
          onActivate={activateSquare}
          onCancel={() => apiRef.current?.selectSquare(null)}
        />
      )}
      {overlay}
    </div>
  );
}

/** Lo que la rejilla lee en voz alta de una casilla. Con la capa de ocupación
 * encendida lo dice ella, que sabe además quién la ataca y quién la defiende
 * —y calla lo que sus marcas tengan apagado, como el panel—; con la capa
 * apagada basta con qué pieza hay, que es lo que hace falta para elegir origen
 * y destino sin ver el tablero. */
function describeBoardSquare(
  fen: string,
  square: string,
  occupancyController: OccupancyController | undefined,
): string {
  if (occupancyController?.occupancy) {
    return describeSquareOccupancy(
      occupancyController.occupancy,
      square,
      occupancyController.marks,
    );
  }
  const piece = readPiecesFromFen(fen)?.[square];
  return `${square}: ${piece ? pieceName(piece.role, piece.color) : "vacía"}`;
}

/** Qué casilla cae bajo un punto de la pantalla, o `null` si cae fuera del
 * tablero. El tablero es un cuadrado de ocho por ocho, así que basta con la
 * fracción del ancho y del alto: eso da la columna y la fila que se ven, y
 * `squaresInReadingOrder` dice qué casilla es cada una desde este lado. */
function squareFromPoint(
  bounds: DOMRect,
  clientX: number,
  clientY: number,
  orientation: "white" | "black",
): string | null {
  const fractionAcross = (clientX - bounds.left) / bounds.width;
  const fractionDown = (clientY - bounds.top) / bounds.height;
  if (fractionAcross < 0 || fractionAcross >= 1 || fractionDown < 0 || fractionDown >= 1) {
    return null;
  }
  const column = Math.floor(fractionAcross * 8);
  const row = Math.floor(fractionDown * 8);
  return squaresInReadingOrder(orientation)[row * 8 + column];
}

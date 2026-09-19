/** Envoltorio de React sobre chessground (el tablero de lichess, GPL-3.0).
 *
 * Chessground tiene una API imperativa y maneja su propio DOM, así que se
 * crea una sola vez con `useRef` y después solo se le pasan actualizaciones
 * con `set()`. Volver a construirlo en cada render rompería las animaciones
 * y perdería el estado de arrastre.
 *
 * La configuración se arma en `buildBoardConfig`, aparte, porque hay que
 * tener cuidado con las claves `undefined` (ver su docstring).
 */
import { Chessground } from "chessground";
import type { Api } from "chessground/api";
import { useEffect, useRef } from "react";
import { buildBoardConfig, type EngineArrow } from "./boardConfig";

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
  /** Al pulsar una casilla en modo editor: es como se coloca una pieza sin
   * arrastrarla, que es lo único que funciona con teclado y con el dedo. */
  onSelectSquare?: (square: string) => void;
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
  onSelectSquare,
  onReady,
}: ChessboardProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const apiRef = useRef<Api | null>(null);
  // Los callbacks se guardan en una ref porque chessground se configura una
  // sola vez: sin esto, los handlers quedarían congelados en los del primer
  // render. Se reasigna en cada render para que apunten siempre a los últimos.
  const handlers = useRef({ onMove, onPositionChange, onSelectSquare });
  handlers.current = { onMove, onPositionChange, onSelectSquare };

  useEffect(() => {
    if (!containerRef.current) return;
    apiRef.current = Chessground(containerRef.current, {
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
      events: {
        change: () => handlers.current.onPositionChange?.(),
        select: (key) => handlers.current.onSelectSquare?.(key),
      },
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
  }, [fen, orientation, engineArrows, lastMoveUci, legalMoves, turnColor]);

  return <div ref={containerRef} className="aspect-square w-full" />;
}

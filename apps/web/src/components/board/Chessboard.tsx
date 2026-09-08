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
}

export function Chessboard({
  fen,
  engineArrows,
  lastMoveUci,
  orientation = "white",
  legalMoves,
  turnColor,
  onMove,
}: ChessboardProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const apiRef = useRef<Api | null>(null);
  // El callback se guarda en una ref porque chessground se configura una sola
  // vez: sin esto, el handler quedaría congelado en el del primer render.
  const onMoveRef = useRef(onMove);
  onMoveRef.current = onMove;

  useEffect(() => {
    if (!containerRef.current) return;
    apiRef.current = Chessground(containerRef.current, {
      ...buildBoardConfig({ fen, orientation, engineArrows, lastMoveUci, legalMoves, turnColor }),
      viewOnly: !onMoveRef.current,
      coordinates: true,
      animation: { enabled: true, duration: 150 },
      movable: {
        free: false,
        color: turnColor,
        dests: legalMoves as never,
        events: { after: (from, to) => onMoveRef.current?.(from, to) },
      },
    });
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

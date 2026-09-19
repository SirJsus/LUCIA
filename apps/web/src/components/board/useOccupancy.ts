/** El estado de la capa de ocupación (RF-7), compartido por las dos pantallas
 * que tienen tablero: el visor de partidas (RF-5) y el tablero de análisis
 * (RF-6). El entrenamiento (RF-4) lo usará igual cuando exista.
 *
 * Vive en un hook y no en cada pantalla porque la capa se comporta igual en
 * todas: los mismos sub-modos, los mismos filtros y el mismo atajo. Tener una
 * copia por pantalla es exactamente lo que abrió el inventario de
 * docs/07-coherencia-ui.md (criterios C-1 y C-2).
 *
 * **De dónde sale lo que se enseña**: entra el FEN de la posición que se está
 * mirando y `computeOccupancy` lo convierte en el mapa de alcances; de ahí
 * beben `OccupancyLayer` (lo pinta sobre el tablero) y `OccupancyPanel` (lo
 * explica al lado). Nada de esto se guarda: la persistencia entre sesiones es
 * RF-7.8, que está en P2 y no entra en la v1.0.
 */
import { useEffect, useMemo, useState } from "react";
import { isTypingTarget } from "../../lib/keyboard";
import { computeOccupancy, type OccupancyMap } from "./occupancy";
import { otherColor, type PieceColor } from "./pieces";

/** Los dos sub-modos de RF-7: el mapa de calor (RF-7.1) colorea el balance de
 * las 64 casillas; la cobertura directa (RF-7.2) enseña solo lo que alcanza un
 * bando. */
export type OccupancyMode = "heatmap" | "coverage";

/** Las tres marcas que se pueden encender sobre el tablero: piezas colgadas
 * (RF-7.4), piezas clavadas (RF-7.6) y rayos X (RF-7.5). */
export type OccupancyMark = "hanging" | "pinned" | "xray";

/** Encendidas de salida: son lo que la capa aporta sobre mirar el tablero a
 * secas, y apagadas de entrada nadie las descubriría. */
const ALL_MARKS_ON: Record<OccupancyMark, boolean> = { hanging: true, pinned: true, xray: true };

/** La tecla que enciende y apaga la capa. Es un acelerador: el control visible
 * está en el panel, y la frase bajo el tablero la anuncia (criterio C-1). */
const OCCUPANCY_TOGGLE_KEY = "o";

export interface OccupancyController {
  /** Si la capa está encendida. Apagada, ni se pinta ni se calcula. */
  isActive: boolean;
  toggle: () => void;
  /** El mapa de la posición actual, o `null` si la capa está apagada o el FEN
   * todavía no se puede leer. */
  occupancy: OccupancyMap | null;
  mode: OccupancyMode;
  setMode: (mode: OccupancyMode) => void;
  /** El bando cuya cobertura se enseña: el que tiene el turno, salvo que se
   * pida ver el otro (RF-7.2). */
  coverageColor: PieceColor;
  isShowingOtherColor: boolean;
  toggleCoverageColor: () => void;
  /** Qué marcas se enseñan sobre el tablero. Las tres se apagan por igual: que
   * una fuera fija obligaría a explicar en el panel por qué esa no se puede
   * quitar (fila 88 del inventario de docs/07-coherencia-ui.md). */
  marks: Record<OccupancyMark, boolean>;
  toggleMark: (mark: OccupancyMark) => void;
  /** La casilla que se está inspeccionando (RF-7.3), fijada al pulsarla. */
  selectedSquare: string | null;
  selectSquare: (square: string) => void;
  /** La casilla por la que pasa el ratón, para filtrar la cobertura al vuelo. */
  hoverSquare: (square: string | null) => void;
  /** La pieza cuya cobertura se está mirando: la señalada con el ratón, o la
   * de la casilla fijada si tiene pieza (RF-7.2). */
  focusedPieceSquare: string | null;
}

export function useOccupancy(fen: string): OccupancyController {
  const [isActive, setIsActive] = useState(false);
  const [mode, setMode] = useState<OccupancyMode>("heatmap");
  const [isShowingOtherColor, setIsShowingOtherColor] = useState(false);
  const [marks, setMarks] = useState(ALL_MARKS_ON);
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
  const [hoveredSquare, setHoveredSquare] = useState<string | null>(null);

  const occupancy = useMemo(() => (isActive ? computeOccupancy(fen) : null), [isActive, fen]);

  // Al cambiar de posición, lo elegido era de la anterior: la casilla fijada
  // tiene otra pieza y la cobertura señalada, otro alcance.
  useEffect(() => {
    setSelectedSquare(null);
    setHoveredSquare(null);
  }, [fen]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      // Con un modificador la tecla es de otro atajo, y escribiendo en un
      // campo es del campo: el filtro de jugador de Partidas lleva "o" en
      // muchos nombres.
      if (event.ctrlKey || event.metaKey || event.altKey || isTypingTarget(event.target)) return;
      if (event.key.toLowerCase() === OCCUPANCY_TOGGLE_KEY) {
        event.preventDefault();
        setIsActive((active) => !active);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const turn = occupancy?.turn ?? "w";
  const hoveredPieceSquare =
    hoveredSquare && occupancy?.pieces[hoveredSquare] ? hoveredSquare : null;
  const selectedPieceSquare =
    selectedSquare && occupancy?.pieces[selectedSquare] ? selectedSquare : null;

  return {
    isActive,
    toggle: () => setIsActive((active) => !active),
    occupancy,
    mode,
    setMode,
    coverageColor: isShowingOtherColor ? otherColor(turn) : turn,
    isShowingOtherColor,
    toggleCoverageColor: () => setIsShowingOtherColor((other) => !other),
    marks,
    toggleMark: (mark) => setMarks((current) => ({ ...current, [mark]: !current[mark] })),
    selectedSquare,
    // Con la capa apagada las dos se ignoran: el tablero avisa igual de cada
    // pulsación y de cada casilla que cruza el ratón, y guardarlas redibujaría
    // la pantalla entera sin que nada de eso se vea.
    //
    // Volver a pulsar la misma casilla la suelta: es la forma de dejar de
    // filtrar la cobertura sin tener que buscar otro control.
    selectSquare: (square) => {
      if (isActive) setSelectedSquare((current) => (current === square ? null : square));
    },
    hoverSquare: (square) => {
      if (isActive) setHoveredSquare(square);
    },
    focusedPieceSquare: hoveredPieceSquare ?? selectedPieceSquare,
  };
}

/** Tablero con su barra de evaluación al lado, tal como aparece en el visor de
 * partidas y en el tablero de análisis (RF-5.2 / RF-6.2).
 *
 * Existe porque el bloque estaba copiado literal en las dos pantallas, con el
 * ancho máximo escrito a mano en cada una: el primer cambio de medida se
 * habría hecho en una sola.
 *
 * La barra se dibuja **siempre**, incluso sin evaluación —ahí se pinta
 * inactiva y con un guion—, por dos motivos: el tablero no se desplaza
 * lateralmente al aparecer y desaparecer, y "el motor todavía no ha dicho
 * nada" es un estado que merece verse (criterio C-3 de
 * docs/07-coherencia-ui.md).
 */
import { Chessboard, type ChessboardProps } from "./Chessboard";
import { EvalBar } from "./EvalBar";

export interface BoardWithEvalBarProps extends ChessboardProps {
  /** Probabilidad de victoria de las blancas (0-100), o `null` si aún no hay
   * evaluación: motor apagado, análisis sin terminar o partida sin analizar. */
  whiteWinPercent: number | null;
}

export function BoardWithEvalBar({ whiteWinPercent, ...boardProps }: BoardWithEvalBarProps) {
  return (
    <div className="mx-auto flex w-full max-w-[36rem] gap-3">
      <EvalBar whiteWinPercent={whiteWinPercent} orientation={boardProps.orientation} />
      <div className="min-w-0 flex-1">
        <Chessboard {...boardProps} />
      </div>
    </div>
  );
}

/** Controles de navegación por las jugadas: inicio, anterior, siguiente y
 * final, con el punto donde estás en medio.
 *
 * Vive aquí, y no dentro del visor, porque el tablero de análisis necesita los
 * mismos: hoy solo responde a ← y →, que hay que saberse (criterio C-1 de
 * docs/07-coherencia-ui.md). El teclado es un acelerador, no la única vía.
 *
 * Los cuatro botones son solo un símbolo, así que todos llevan nombre
 * accesible; `position` es el texto del medio, que cada pantalla cuenta a su
 * manera (jugada de la partida, o posición dentro de la línea actual).
 */
import { Button } from "../Button";

export interface MoveNavigatorProps {
  onFirst: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onLast: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
  position: string;
}

export function MoveNavigator({
  onFirst,
  onPrevious,
  onNext,
  onLast,
  canGoBack,
  canGoForward,
  position,
}: MoveNavigatorProps) {
  return (
    <div className="flex items-center justify-center gap-2 text-sm">
      <NavButton onClick={onFirst} disabled={!canGoBack} symbol="⏮" accessibleName="Ir al principio" />
      <NavButton onClick={onPrevious} disabled={!canGoBack} symbol="◀" accessibleName="Jugada anterior" />
      <span className="w-28 text-center tabular-nums opacity-70">{position}</span>
      <NavButton onClick={onNext} disabled={!canGoForward} symbol="▶" accessibleName="Jugada siguiente" />
      <NavButton onClick={onLast} disabled={!canGoForward} symbol="⏭" accessibleName="Ir al final" />
    </div>
  );
}

function NavButton({
  onClick,
  disabled,
  symbol,
  accessibleName,
}: {
  onClick: () => void;
  disabled: boolean;
  symbol: string;
  accessibleName: string;
}) {
  return (
    <Button
      size="sm"
      onClick={onClick}
      disabled={disabled}
      aria-label={accessibleName}
      title={accessibleName}
      className="px-2.5 py-1 text-base leading-none"
    >
      {symbol}
    </Button>
  );
}

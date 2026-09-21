/** Un drill de apertura en pantalla (RF-4.2): el tablero donde se repite la
 * línea y el panel que dice qué se entrena y por qué.
 *
 * **La línea no está aquí.** Mientras el drill está abierto, el navegador solo
 * sabe la posición que tiene delante: cada jugada se manda al servidor, que
 * comprueba, contesta por el rival y devuelve la posición siguiente. Es la
 * misma razón que en los puzzles (`PuzzleSolver`), y aquí además es lo que
 * permite que el rival responda sin que el navegador sepa qué viene.
 *
 * **Por dónde va el drill lo lleva este componente** (`ply`), como el número
 * de intento de un puzzle: el ciclo es suyo. El servidor no guarda progreso —
 * un drill se repite entero o no se repite—, así que el estado vive aquí y se
 * reinicia solo montando el componente con `key={drill.id}`.
 */
import type { Drill, DrillMove } from "@lucia/shared-types";
import { useMutation } from "@tanstack/react-query";
import { Chess } from "chess.js";
import { useMemo, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Chessboard } from "../../components/board/Chessboard";
import { legalMovesByOrigin } from "../../components/board/legalMoves";
import { ErrorBox, SuccessBox, WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { BOARD_HINT_CLASSES, BOARD_SIDEBAR_GRID_CLASS } from "../../components/styles";
import { api } from "../../lib/api";
import { moveNumberOf } from "../../lib/moves";
import { playerMoveCount, reasonLabel, reasonSentence } from "./drills";

export function DrillRunner({ drill, onNext }: { drill: Drill; onNext: () => void }) {
  /** La posición que se ve y en qué jugada de la línea va. Arrancan donde la
   * cola dijo: con negras, el rival ya ha abierto. */
  const [fen, setFen] = useState(drill.fen);
  const [ply, setPly] = useState(drill.first_player_ply);
  /** Cuántas veces se ha fallado en esta pasada. Es lo que distingue después
   * recorrer la línea limpia de recorrerla tropezando. */
  const [wrongMoves, setWrongMoves] = useState(0);
  const [wasWrong, setWasWrong] = useState(false);
  const [lastMoveUci, setLastMoveUci] = useState<string | null>(null);

  const color = drill.player_color === "black" ? "black" : "white";

  const moveMutation = useMutation({
    mutationFn: (uci: string | null) =>
      api.playDrillMove(drill.id, { ply, uci, wrong_moves: wrongMoves }),
    onSuccess: (result, uci) => applyResult(result, uci),
  });
  /** La respuesta que cerró la línea, o `null` si el drill sigue abierto.
   * Se lee de la última respuesta en vez de guardarse aparte: es la misma que
   * trae la línea entera y el próximo repaso, y cerrado ya no se manda nada
   * más (igual que `PuzzleSolver` con su respuesta). */
  const finished = moveMutation.data?.finished ? moveMutation.data : null;

  function applyResult(result: DrillMove, uci: string | null) {
    setFen(result.fen);
    if (result.finished) {
      setLastMoveUci(null);
      return;
    }
    if (!result.correct) {
      setWrongMoves(wrongMoves + 1);
      setWasWrong(true);
      return;
    }
    setWasWrong(false);
    setLastMoveUci(result.reply_uci ?? uci);
    setPly(result.next_ply ?? ply);
  }

  /** El tablero deja mover mientras el drill esté abierto y no haya una
   * petición en vuelo: acertar trae la respuesta del rival, así que mover dos
   * veces seguidas sería mover sobre una posición que ya no es la de la
   * pantalla (criterio C-3). */
  const canMove = finished === null && !moveMutation.isPending;
  const legalMoves = useMemo(() => (canMove ? legalMovesByOrigin(fen) : undefined), [canMove, fen]);

  function tryMove(from: string, to: string) {
    if (!canMove) return;
    const chess = new Chess(fen);
    try {
      // La promoción siempre a dama, como en el resto de tableros.
      const move = chess.move({ from, to, promotion: "q" });
      moveMutation.mutate(move.lan);
    } catch {
      // jugada ilegal; chessground ya filtra casi todas
    }
  }

  const totalMoves = playerMoveCount(drill);
  return (
    <div className={BOARD_SIDEBAR_GRID_CLASS}>
      <div className="space-y-2">
        {/* Sin barra de evaluación, como en los puzzles: lo que se entrena es
            recordar la línea, y una evaluación en pantalla la delata. */}
        <Chessboard
          fen={fen}
          orientation={color}
          turnColor={color}
          legalMoves={legalMoves}
          onMove={tryMove}
          lastMoveUci={lastMoveUci}
        />
        <p className={BOARD_HINT_CLASSES}>
          {finished
            ? "La línea terminó: el tablero ya no se mueve."
            : "Arrastra una pieza para seguir la línea. Las promociones se coronan en dama."}
        </p>
      </div>

      <aside className="space-y-3">
        <Panel
          title={drill.opening_name ?? "Línea de apertura"}
          aside={<Badge tone={drill.reason === "departure" ? "warning" : "info"}>
            {reasonLabel(drill.reason)}
          </Badge>}
        >
          <p className="text-sm">
            Juegas con {color === "white" ? "blancas" : "negras"}
            {drill.opening_eco ? ` · ${drill.opening_eco}` : ""}
          </p>
          <p className="mt-1 text-xs opacity-70">{reasonSentence(drill)}</p>
          {drill.preceding_moves_san.length > 0 && (
            <p className="mt-2 text-xs opacity-70">
              La línea empieza con {drill.preceding_moves_san.join(" ")}.
            </p>
          )}
          <p className="mt-2 text-sm">
            {finished
              ? `${totalMoves} ${totalMoves === 1 ? "jugada" : "jugadas"} en la línea.`
              : /* El número de jugada sale de `lib/moves.ts`, como en las
                   seis pantallas que numeran (criterio C-5): una línea
                   arranca en la posición estándar, así que la jugada propia
                   que toca cae justo en ese turno. */
                `Jugada ${moveNumberOf(ply)} de ${totalMoves}.`}
          </p>
        </Panel>

        {moveMutation.isError && <ErrorBox error={moveMutation.error} />}

        {wasWrong && !finished && (
          <WarningBox>
            <p>
              Esa no es la jugada de la línea.{" "}
              {wrongMoves === 1 ? "Es tu primer fallo." : `Llevas ${wrongMoves} fallos.`} Prueba
              otra.
            </p>
          </WarningBox>
        )}

        {/* Rendirse es una sola acción, con un solo nombre y siempre en el
            mismo sitio mientras el drill esté abierto (criterio C-2). */}
        {!finished && (
          <Button disabled={moveMutation.isPending} onClick={() => moveMutation.mutate(null)}>
            {moveMutation.isPending ? "Comprobando…" : "Ver la línea"}
          </Button>
        )}

        {finished && <DrillResult drill={drill} result={finished} onNext={onNext} />}
      </aside>
    </div>
  );
}

function DrillResult({
  drill,
  result,
  onNext,
}: {
  drill: Drill;
  result: DrillMove;
  onNext: () => void;
}) {
  return (
    <>
      {result.correct ? (
        <SuccessBox>Línea completa.</SuccessBox>
      ) : (
        <WarningBox>La línea era esta.</WarningBox>
      )}

      <Panel title="La línea">
        <p className="text-sm">{result.line_san.join(" ")}</p>
        <p className="mt-1 text-xs opacity-70">
          {drill.reason === "departure"
            ? "La última jugada es la que los maestros hacen aquí, en lugar de la que tú haces."
            : "Es la línea principal de esta apertura hasta donde te separas de ella."}
        </p>
      </Panel>

      <Panel title="Próximo repaso">
        <p className="text-sm">
          {result.interval_days === 1
            ? "Vuelve mañana."
            : `Vuelve dentro de ${result.interval_days} días.`}
        </p>
        <p className="mt-1 text-xs opacity-70">
          {result.correct
            ? "Se espacia cada vez que la recorres entera."
            : "Un fallo la devuelve al principio de la cola."}
        </p>
      </Panel>

      <Button variant="primary" onClick={onNext}>
        Siguiente línea
      </Button>
    </>
  );
}

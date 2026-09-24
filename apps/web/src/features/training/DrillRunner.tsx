/** Un drill de apertura en pantalla (RF-4.2): el tablero donde se repite la
 * línea, la capa de ocupación que se enciende sobre él (RF-7) y el panel que
 * dice qué se entrena y por qué.
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
import { useState } from "react";
import { Button } from "../../components/Button";
import { RETRY_AFTER_WRONG_MOVE_HINT } from "../../components/board/hints";
import { ErrorBox, SuccessBox, WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { BOARD_SIDEBAR_GRID_CLASS } from "../../components/styles";
import { api } from "../../lib/api";
import { formatMoveSequence, moveNumberOf, tryMove } from "../../lib/moves";
import { drillSourceLabel, drillSourceSentence, playerMoveCount } from "./drills";
import { TrainingStatusBadge } from "./TrainingStatusBadge";
import { TrainingBoard } from "./TrainingBoard";

export function DrillRunner({ drill, onNext }: { drill: Drill; onNext: () => void }) {
  /** La posición que se ve y en qué jugada de la línea va. Arrancan donde la
   * cola dijo: con negras, el rival ya ha abierto. */
  const [fen, setFen] = useState(drill.fen);
  const [ply, setPly] = useState(drill.first_player_ply);
  /** Cuántas veces se ha fallado en esta pasada. Es lo que distingue después
   * recorrer la línea limpia de recorrerla tropezando. */
  const [wrongMoves, setWrongMoves] = useState(0);
  const [lastMoveUci, setLastMoveUci] = useState<string | null>(null);
  /** La jugada que se acaba de soltar, puesta sobre el tablero mientras el
   * servidor contesta. Si era la de la línea se borra en cuanto llega la
   * respuesta del rival; si no lo era **se queda ahí** y hay que pulsar
   * «Volver a intentarlo», como en los puzzles: borrarla al instante da la
   * sensación de que la pieza rebotó y no de que la respuesta era otra
   * (fila 97 del inventario de docs/07-coherencia-ui.md). */
  const [attemptedMove, setAttemptedMove] = useState<{
    fen: string;
    uci: string;
  } | null>(null);

  const color = drill.player_color === "black" ? "black" : "white";

  const moveMutation = useMutation({
    mutationFn: (uci: string | null) =>
      api.playDrillMove(drill.id, { ply, uci, wrong_moves: wrongMoves }),
    onSuccess: (moveResult, uci) => applyMoveResult(moveResult, uci),
  });
  /** La respuesta que cerró la línea, o `null` si el drill sigue abierto.
   * Se lee de la última respuesta en vez de guardarse aparte: es la misma que
   * trae la línea entera y el próximo repaso, y cerrado ya no se manda nada
   * más (igual que `PuzzleSolver` con su respuesta). */
  const reviewedMove = moveMutation.data?.reviewed ? moveMutation.data : null;
  /** Si la última respuesta dijo que la jugada no era la de la línea. Se lee de
   * la respuesta y no se guarda aparte —como `reviewedMove`, y como el fallo de
   * `PuzzleSolver`—: el estado propio de aquí es la jugada que quedó encima del
   * tablero, y haber fallado es lo que el servidor contestó de ella. */
  const wasWrong = moveMutation.data?.reviewed === false && !moveMutation.data.correct;

  function applyMoveResult(moveResult: DrillMove, uci: string | null) {
    // Fallar es lo único que deja el tablero como estaba: la jugada errónea
    // sigue encima hasta que se pulse «Volver a intentarlo».
    if (!moveResult.reviewed && !moveResult.correct) {
      setWrongMoves(wrongMoves + 1);
      return;
    }
    setAttemptedMove(null);
    setFen(moveResult.fen);
    if (moveResult.reviewed) {
      setLastMoveUci(null);
      return;
    }
    setLastMoveUci(moveResult.reply_uci ?? uci);
    setPly(moveResult.next_ply ?? ply);
  }

  /** Quitar del tablero la jugada errónea y volver a la posición de la línea,
   * igual que en `PuzzleSolver`: `reset()` olvida la respuesta que dijo que
   * estaba mal. `wrongMoves` no se toca: los fallos de la pasada se siguen
   * contando. */
  function retry() {
    setAttemptedMove(null);
    moveMutation.reset();
  }

  /** El tablero deja mover mientras el drill esté abierto y no haya una
   * petición en vuelo: acertar trae la respuesta del rival, así que mover dos
   * veces seguidas sería mover sobre una posición que ya no es la de la
   * pantalla (criterio C-3). */
  const canMove = reviewedMove === null && !moveMutation.isPending && attemptedMove === null;
  /** Lo que se ve: la posición de la línea, o la jugada intentada encima. */
  const shownFen = attemptedMove?.fen ?? fen;

  function handleMove(from: string, to: string) {
    if (!canMove) return;
    const move = tryMove(fen, from, to);
    if (!move) return;
    setAttemptedMove({ fen: move.fen, uci: move.uci });
    moveMutation.mutate(move.uci);
  }

  const playerMoveTotal = playerMoveCount(drill);
  return (
    <div className={BOARD_SIDEBAR_GRID_CLASS}>
      <TrainingBoard
        fen={shownFen}
        color={color}
        canMove={canMove}
        onMove={handleMove}
        lastMoveUci={attemptedMove?.uci ?? lastMoveUci}
        acceptsMoves={reviewedMove === null && !wasWrong}
        hint={
          reviewedMove
            ? "La línea terminó: el tablero ya no se mueve."
            : wasWrong
              ? RETRY_AFTER_WRONG_MOVE_HINT
              : "Arrastra una pieza para seguir la línea. Las promociones se coronan en dama."
        }
      />

      <aside className="space-y-3">
        {/* El mismo título y la misma insignia que el puzzle y el sparring:
            qué bando llevas arriba y qué está pasando al lado, y lo que
            identifica al ejercicio —la apertura, en qué repaso va— en el
            cuerpo (fila 98 del inventario, criterios C-2 y C-3). */}
        <Panel
          title={`Juegas con ${color === "white" ? "blancas" : "negras"}`}
          aside={
            <TrainingStatusBadge
              isPlayerTurn={reviewedMove === null}
              isWaitingForServer={moveMutation.isPending}
              finishedLabel="línea terminada"
            />
          }
        >
          <p className="text-sm">
            {drill.opening_name ?? "Línea de apertura"}
            {drill.opening_eco ? ` · ${drill.opening_eco}` : ""}
          </p>
          <p className="mt-1 text-xs opacity-70">
            {drillSourceLabel(drill.source)}: {drillSourceSentence(drill)}
          </p>
          {/* En qué repaso va, como el puzzle: la API lo manda (`repetitions`)
              y era el único de los tres ejercicios que no lo enseñaba. */}
          <p className="mt-1 text-xs opacity-70">
            {drill.repetitions > 0
              ? `Ya la has recorrido entera ${drill.repetitions} ${
                  drill.repetitions === 1 ? "vez" : "veces"
                }; vuelves para afianzarla.`
              : "Es la primera vez que la recorres."}
          </p>
          {drill.preceding_moves_san.length > 0 && (
            <p className="mt-2 text-xs opacity-70">
              La línea empieza con{" "}
              <span className="font-mono">{formatMoveSequence(drill.preceding_moves_san)}</span>.
            </p>
          )}
          <p className="mt-2 text-sm">
            {reviewedMove
              ? `${playerMoveTotal} ${playerMoveTotal === 1 ? "jugada" : "jugadas"} en la línea.`
              : /* El número de jugada sale de `lib/moves.ts`, como en las
                   seis pantallas que numeran (criterio C-5): una línea
                   arranca en la posición estándar, así que la jugada propia
                   que toca cae justo en ese turno. */
                `Jugada ${moveNumberOf(ply)} de ${playerMoveTotal}.`}
          </p>
        </Panel>

        {/* `onRetry` recupera la posición de la línea, que es lo que desbloquea
            la pantalla: si la petición falla por red, la jugada intentada se
            queda encima y el tablero no deja mover, porque el botón de volver
            a intentarlo cuelga de que el servidor haya contestado "mal"
            (criterio C-3: de un error se tiene que poder salir). Es el mismo
            arreglo y en el mismo sitio que en `PuzzleSolver`. */}
        {moveMutation.isError && <ErrorBox error={moveMutation.error} onRetry={retry} />}

        {wasWrong && (
          <WarningBox>
            <p>
              Esa no es la jugada de la línea.{" "}
              {wrongMoves === 1 ? "Es tu primer fallo." : `Llevas ${wrongMoves} fallos.`}
            </p>
            <div className="mt-2">
              <Button size="sm" variant="primary" onClick={retry}>
                Volver a intentarlo
              </Button>
            </div>
          </WarningBox>
        )}

        {/* Rendirse es una sola acción, con un solo nombre y siempre en el
            mismo sitio mientras el drill esté abierto (criterio C-2). */}
        {!reviewedMove && (
          <Button disabled={moveMutation.isPending} onClick={() => moveMutation.mutate(null)}>
            {moveMutation.isPending ? "Comprobando…" : "Ver la línea"}
          </Button>
        )}

        {reviewedMove && <DrillResult drill={drill} moveResult={reviewedMove} onNext={onNext} />}
      </aside>
    </div>
  );
}

function DrillResult({
  drill,
  moveResult,
  onNext,
}: {
  drill: Drill;
  moveResult: DrillMove;
  onNext: () => void;
}) {
  return (
    <>
      {moveResult.correct ? (
        <SuccessBox>Línea completa.</SuccessBox>
      ) : (
        <WarningBox>La línea era esta.</WarningBox>
      )}

      <Panel title="La línea">
        <p className="font-mono text-sm">{formatMoveSequence(moveResult.line_moves_san)}</p>
        <p className="mt-1 text-xs opacity-70">
          {drill.source === "departure"
            ? "La última jugada es la que los maestros hacen aquí, en lugar de la que tú haces."
            : "Es la línea principal de esta apertura hasta donde te separas de ella."}
        </p>
      </Panel>

      <Panel title="Próximo repaso">
        <p className="text-sm">
          {moveResult.interval_days === 1
            ? "Vuelve mañana."
            : `Vuelve dentro de ${moveResult.interval_days} días.`}
        </p>
        <p className="mt-1 text-xs opacity-70">
          {moveResult.correct
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

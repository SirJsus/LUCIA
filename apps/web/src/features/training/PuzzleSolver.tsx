/** Un puzzle en pantalla: el tablero donde se intenta la jugada y el panel
 * que dice cómo fue (RF-4.1).
 *
 * **La comprobación la hace el servidor.** Aquí no se sabe cuál es la
 * solución mientras el puzzle está abierto, y es deliberado: cualquier cosa
 * que llegara al navegador se podría leer, y son varias las jugadas buenas
 * (RF-10.3), no una. Este componente solo manda la jugada intentada y cuenta
 * los intentos, que es lo que distingue después acertar a la primera de
 * acertar tropezando.
 *
 * El estado del intento vive aquí y no en la pantalla: quien la usa monta
 * este componente con `key={puzzle.id}`, así que cambiar de puzzle lo
 * reinicia solo.
 */
import type { Puzzle, PuzzleAnswer } from "@lucia/shared-types";
import { useMutation } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useMemo, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { ClassificationBadge } from "../../components/ClassificationBadge";
import { Chessboard } from "../../components/board/Chessboard";
import type { EngineArrow } from "../../components/board/boardConfig";
import { legalMovesByOrigin } from "../../components/board/legalMoves";
import { arrowsFromPuzzleAnswer } from "./arrows";
import { ErrorBox, SuccessBox, WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import {
  BOARD_HINT_CLASSES,
  BOARD_SIDEBAR_GRID_CLASS,
  buttonClasses,
} from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate, formatOwnWinPercentLossSentence } from "../../lib/format";
import { moveNumberLabel, plyFromFen } from "../../lib/moves";

export function PuzzleSolver({ puzzle, onNext }: { puzzle: Puzzle; onNext: () => void }) {
  /** La posición que se ve. Es la del puzzle salvo justo después de un
   * intento fallido, donde se deja la jugada hecha sobre el tablero: borrarla
   * al instante da la sensación de que la pieza rebotó y no de que la
   * respuesta era otra. */
  const [shownFen, setShownFen] = useState(puzzle.fen);
  const [attemptedUci, setAttemptedUci] = useState<string | null>(null);
  /** Cuántas veces se ha intentado, contando la que está en curso. */
  const [attempt, setAttempt] = useState(1);
  /** El bando de quien resuelve, que es el del turno: orienta el tablero y es
   * el único que puede mover. */
  const color = puzzle.color === "black" ? "black" : "white";

  const answerMutation = useMutation({
    mutationFn: ({ uci, attempt }: { uci: string | null; attempt: number }) =>
      api.answerPuzzle(puzzle.id, { uci, attempt }),
  });
  const answer = answerMutation.data;
  /** La respuesta cuando el puzzle ya está cerrado, o `null` si sigue
   * abierto. Mientras lo está, el servidor manda a `null` todo lo que lo
   * resolvería, así que solo desde aquí se puede leer sin comprobar nada. */
  const reviewedAnswer = answer ? asReviewed(answer) : null;
  const isReviewed = reviewedAnswer !== null;
  const isWrongAndOpen = answer !== undefined && !answer.reviewed;

  /** El tablero solo deja mover cuando lo que se ve es la posición del
   * puzzle. Tras fallar se queda con la jugada errónea encima, y entonces
   * arrastrar ahí movería piezas de una posición distinta de la que hay en
   * pantalla: hay que pulsar «Volver a intentarlo» primero (criterio C-3). */
  const legalMoves = useMemo(
    () => (shownFen === puzzle.fen ? legalMovesByOrigin(puzzle.fen) : undefined),
    [puzzle.fen, shownFen],
  );
  const arrows = useMemo(
    () =>
      reviewedAnswer
        ? arrowsFromPuzzleAnswer(
            puzzle.fen,
            reviewedAnswer.solutions_san,
            reviewedAnswer.played_san,
          )
        : [],
    [puzzle.fen, reviewedAnswer],
  );

  function tryMove(from: string, to: string) {
    if (isReviewed || answerMutation.isPending) return;

    const chess = new Chess(puzzle.fen);
    try {
      // La promoción siempre a dama, igual que en el tablero de análisis.
      const move = chess.move({ from, to, promotion: "q" });
      setShownFen(chess.fen());
      setAttemptedUci(move.lan);
      answerMutation.mutate(
        { uci: move.lan, attempt },
        {
          onSuccess: (result) => {
            if (!result.reviewed) setAttempt(attempt + 1);
          },
        },
      );
    } catch {
      // jugada ilegal; chessground ya filtra casi todas
    }
  }

  function retry() {
    setShownFen(puzzle.fen);
    setAttemptedUci(null);
    answerMutation.reset();
  }

  return (
    <div className={BOARD_SIDEBAR_GRID_CLASS}>
      <div className="space-y-2">
        {/* Sin barra de evaluación, al contrario que el visor y el tablero de
            análisis: aquí la evaluación de la posición es media respuesta.
            Aparece al cerrar el puzzle, en números, dentro del panel. */}
        <Chessboard
          fen={shownFen}
          orientation={color}
          turnColor={color}
          legalMoves={legalMoves}
          onMove={tryMove}
          lastMoveUci={attemptedUci}
          engineArrows={arrows}
        />
        {/* Lo que hay que saber del tablero, en la misma frase y con la misma
            forma que en el visor y en el tablero de análisis (criterio C-1).
            Con el puzzle cerrado el tablero ya no se mueve y lo que hay que
            saber es qué significa cada flecha: el color no puede ser lo único
            que lo diga (criterios C-6 y C-7), como ya hace la leyenda de la
            capa de ocupación. */}
        <p className={BOARD_HINT_CLASSES}>
          {isReviewed
            ? arrowLegend(arrows)
            : "Arrastra una pieza para responder. Las promociones se coronan en dama."}
        </p>
      </div>

      <aside className="space-y-3">
        <Panel
          title={color === "white" ? "Juegan blancas" : "Juegan negras"}
          aside={
            puzzle.repetitions > 0 ? (
              <Badge tone="info" title="Ya lo has acertado antes; vuelve para afianzarlo">
                repaso {puzzle.repetitions + 1}
              </Badge>
            ) : (
              <Badge tone="neutral">nuevo</Badge>
            )
          }
        >
          <p className="text-sm">
            {isReviewed
              ? "Aquí es donde se torció la partida."
              : "Encuentra la jugada que hacía falta aquí."}
          </p>
          <p className="mt-2 text-xs opacity-70">
            De tu partida contra {puzzle.opponent}, {formatDate(puzzle.played_at)}, en la jugada{" "}
            {moveNumberLabel(plyFromFen(puzzle.fen))}
          </p>
        </Panel>

        {answerMutation.isError && <ErrorBox error={answerMutation.error} />}

        {isWrongAndOpen && (
          <WarningBox>
            {/* `attempt` es el intento que viene, así que los hechos son uno
                menos: tras fallar el primero decía "llevas 2 intentos", y con
                el singular escribía "1 intentos". */}
            <p>
              Esa no es la jugada.{" "}
              {attempt === 2 ? "Es tu primer intento." : `Llevas ${attempt - 1} intentos.`}
            </p>
            <div className="mt-2">
              <Button size="sm" variant="primary" onClick={retry}>
                Volver a intentarlo
              </Button>
            </div>
          </WarningBox>
        )}

        {/* Rendirse es una sola acción, con un solo nombre, un solo tamaño y
            siempre en el mismo sitio mientras el puzzle esté abierto: estaba
            dos veces —suelta antes de responder y dentro del aviso tras
            fallar, en `md` y en `sm`— y cambiaba de posición al fallar
            (criterio C-2). */}
        {!isReviewed && (
          <Button
            disabled={answerMutation.isPending}
            onClick={() => answerMutation.mutate({ uci: null, attempt })}
          >
            {answerMutation.isPending ? "Comprobando…" : "Ver la solución"}
          </Button>
        )}

        {reviewedAnswer && (
          <PuzzleResult puzzle={puzzle} answer={reviewedAnswer} onNext={onNext} />
        )}
      </aside>
    </div>
  );
}

/** Qué significa cada flecha del tablero, y solo las que están dibujadas: una
 * leyenda que nombra un color que no se ve manda a buscarlo (es la misma
 * regla que sigue la leyenda de la capa de ocupación). */
function arrowLegend(arrows: EngineArrow[]): string {
  const parts = ["Flecha verde: la jugada que hacía falta"];
  if (arrows.some((arrow) => arrow.brush === "paleGreen")) {
    parts.push("verde claro: las demás que valían");
  }
  if (arrows.some((arrow) => arrow.brush === "red")) {
    parts.push("roja: la que se jugó en la partida");
  }
  return `${parts.join("; ")}.`;
}

/** La respuesta de un puzzle ya cerrado. Es la misma de la API con los
 * campos que solo viajan al cerrarlo ya sin `null`: mientras el puzzle sigue
 * abierto llegan vacíos a propósito, porque la evaluación del error y la
 * clasificación de la jugada son media respuesta. */
type ReviewedPuzzleAnswer = PuzzleAnswer & {
  classification: string;
  win_percent_before: number;
  win_percent_after: number;
  interval_days: number;
};

function asReviewed(answer: PuzzleAnswer): ReviewedPuzzleAnswer | null {
  const { classification, win_percent_before, win_percent_after, interval_days } = answer;
  if (
    !answer.reviewed ||
    classification === null ||
    win_percent_before === null ||
    win_percent_after === null ||
    interval_days === null
  ) {
    return null;
  }
  return { ...answer, classification, win_percent_before, win_percent_after, interval_days };
}

function PuzzleResult({
  puzzle,
  answer,
  onNext,
}: {
  puzzle: Puzzle;
  answer: ReviewedPuzzleAnswer;
  onNext: () => void;
}) {
  return (
    <>
      {answer.correct ? (
        <SuccessBox>Correcto: {answer.solutions_san[0]}.</SuccessBox>
      ) : (
        <WarningBox>La jugada era {answer.solutions_san[0]}.</WarningBox>
      )}

      <Panel title="Lo que pasó en la partida">
        <p className="flex items-center gap-2 text-sm">
          <span>Jugaste {answer.played_san}</span>
          <ClassificationBadge classification={answer.classification} />
        </p>
        {/* La frase sale de `lib/format.ts`, que es donde vive el formateo, y
            no escrita aquí: la lista de re-jugar (RF-4.4) dice exactamente lo
            mismo del mismo dato (criterio C-5). */}
        <p className="mt-1 text-xs opacity-70">
          {formatOwnWinPercentLossSentence(answer.win_percent_before, answer.win_percent_after)}
        </p>
        {answer.solutions_san.length > 1 && (
          <p className="mt-2 text-xs opacity-70">
            {/* RF-10.3: no hay una sola respuesta buena, y decirlo es parte de
                lo que se viene a aprender. */}
            También valían {answer.solutions_san.slice(1).join(", ")}.
          </p>
        )}
      </Panel>

      <Panel title="Próximo repaso">
        <p className="text-sm">
          {answer.interval_days === 1
            ? "Vuelve mañana."
            : `Vuelve dentro de ${answer.interval_days} días.`}
        </p>
        <p className="mt-1 text-xs opacity-70">
          {answer.correct
            ? "Se espacia cada vez que lo aciertas."
            : "Un fallo lo devuelve al principio de la cola."}
        </p>
      </Panel>

      <div className="flex gap-2">
        <Button variant="primary" onClick={onNext}>
          Siguiente puzzle
        </Button>
        <Link
          to="/games/$gameId"
          params={{ gameId: String(puzzle.game_id) }}
          className={buttonClasses()}
        >
          {/* "Ver partida" es como se llama ir a una partida en las otras dos
              pantallas que llevan a una (criterio C-2). */}
          Ver partida
        </Link>
      </div>
    </>
  );
}

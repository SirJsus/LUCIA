/** Tablero de análisis (RF-6.2 a RF-6.5): mover piezas, ramificar variantes,
 * ver lo que dice el motor en vivo y autoguardar.
 *
 * El tablero, la barra de evaluación, las flechas y los controles de
 * navegación se comparten con el visor de partidas: viven en
 * `components/board/` (`Chessboard`, `EvalBar`, `BoardWithEvalBar`,
 * `MoveNavigator`, `boardConfig`) para que las dos pantallas enseñen lo mismo
 * de la misma forma. Lo propio de aquí es el árbol de variantes (`tree.ts`,
 * `VariationTree`) y el panel del motor (`EngineLines`).
 *
 * La cabecera coloca las acciones en el mismo orden que el visor —girar
 * tablero, motor, acción principal— porque tenerlas en orden distinto obliga a
 * buscarlas cada vez que se cambia de pantalla (criterio C-2 de
 * docs/07-coherencia-ui.md). */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/Button";
import { EngineSelect } from "../../components/EngineSelect";
import { BoardWithEvalBar } from "../../components/board/BoardWithEvalBar";
import { MoveNavigator } from "../../components/board/MoveNavigator";
import { useMoveNavigationKeys } from "../../components/board/useMoveNavigationKeys";
import { arrowsFromEngineLines, arrowsFromPreviewLine } from "../../components/board/boardConfig";
import { ErrorBox, Spinner, SuccessBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import { BOARD_HINT_CLASSES, BOARD_SIDEBAR_GRID_CLASS } from "../../components/styles";
import { api } from "../../lib/api";
import { type EngineId } from "../../lib/format";
import { whiteWinPercentFromScore } from "../../lib/score";
import { EngineLines } from "./EngineLines";
import { VariationTree } from "./VariationTree";
import {
  addMove,
  createRoot,
  deleteNode,
  findNode,
  isTreeNode,
  mainLine,
  pathToNode,
  promoteNode,
  toPgn,
  type TreeNode,
} from "./tree";

/** Espera antes de guardar y antes de pedir análisis. Sin esto, cada jugada
 * en una secuencia rápida lanzaría su propia petición. */
const AUTOSAVE_DELAY_MS = 800;
const ANALYSIS_DELAY_MS = 400;

export function BoardPage() {
  const { boardId } = useParams({ from: "/boards/$boardId" });
  const id = Number(boardId);

  const boardQuery = useQuery({ queryKey: ["board", id], queryFn: () => api.getBoard(id) });

  const [tree, setTree] = useState<TreeNode | null>(null);
  const [currentId, setCurrentId] = useState("root");
  const [orientation, setOrientation] = useState<"white" | "black">("white");
  const [engine, setEngine] = useState<EngineId>("stockfish");
  const [engineOn, setEngineOn] = useState(true);
  const [previewPvUci, setPreviewPvUci] = useState<string[] | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  // Carga inicial del árbol guardado. Un `tree_json` con forma inesperada
  // (versión anterior, edición manual) no debe romper la pantalla: se empieza
  // de cero desde el FEN raíz, que sí es fiable.
  useEffect(() => {
    if (!boardQuery.data || tree) return;
    const savedTree = boardQuery.data.tree_json;
    setTree(isTreeNode(savedTree) ? savedTree : createRoot(boardQuery.data.root_fen));
  }, [boardQuery.data, tree]);

  const saveMutation = useMutation({
    mutationFn: (updated: TreeNode) => api.updateBoard(id, { tree_json: updated }),
    onSuccess: () => setSaveState("saved"),
    // Sin esto la cabecera se quedaba en "Guardando…" para siempre mientras
    // un recuadro de error decía lo contrario dos líneas más abajo.
    onError: () => setSaveState("error"),
  });

  // Marcar el tablero como partida propia cambia lo que cuenta en las
  // estadísticas (RF-6.5): es una escritura y se trata como tal, con estado
  // de envío y error a la vista.
  const ownGameMutation = useMutation({
    mutationFn: (isOwnGame: boolean) => api.updateBoard(id, { is_own_game: isOwnGame }),
    onSuccess: () => boardQuery.refetch(),
  });

  const copyPgnMutation = useMutation({
    mutationFn: (pgn: string) => navigator.clipboard.writeText(pgn),
  });

  // Autoguardado con retardo (RF-6.8).
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scheduleSave = useCallback(
    (updated: TreeNode) => {
      setSaveState("saving");
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => saveMutation.mutate(updated), AUTOSAVE_DELAY_MS);
    },
    [saveMutation],
  );
  useEffect(() => () => void (saveTimer.current && clearTimeout(saveTimer.current)), []);

  const currentNode = tree ? (findNode(tree, currentId) ?? tree) : null;
  const currentFen = currentNode?.fen ?? "";

  // El análisis se pide con retardo para no lanzar una petición por cada
  // jugada mientras se avanza rápido por una línea.
  const [analysisFen, setAnalysisFen] = useState("");
  useEffect(() => {
    if (!engineOn || !currentFen) return;
    const timer = setTimeout(() => setAnalysisFen(currentFen), ANALYSIS_DELAY_MS);
    return () => clearTimeout(timer);
  }, [currentFen, engineOn]);

  // Mientras el retardo no ha vencido, lo que hay en pantalla es la evaluación
  // de la posición anterior. Callarlo hace que la barra contradiga al tablero
  // durante una secuencia rápida de jugadas (criterio C-3).
  const isEvaluationStale = engineOn && currentFen !== "" && analysisFen !== currentFen;

  const analysisQuery = useQuery({
    queryKey: ["position", analysisFen, engine],
    queryFn: () => api.analyzePosition({ fen: analysisFen, engine }),
    enabled: engineOn && analysisFen !== "",
    staleTime: Infinity, // la evaluación de una posición no cambia sola
  });

  // Al cambiar de posición, la línea previsualizada deja de tener sentido:
  // sus jugadas eran continuaciones de la posición anterior. Se limpia aquí y
  // no en cada acción porque la posición cambia por muchas vías (jugar,
  // teclado, árbol de variantes).
  useEffect(() => setPreviewPvUci(null), [currentId]);

  // Lo que se dibuja sobre el tablero: la línea que se está señalando en el
  // panel manda sobre las recomendaciones del motor, porque es lo que el
  // usuario está mirando en ese momento.
  const bestLine = analysisQuery.data?.[0];
  const engineArrows = useMemo(
    () =>
      previewPvUci
        ? arrowsFromPreviewLine(previewPvUci)
        : engineOn
          ? arrowsFromEngineLines(analysisQuery.data)
          : [],
    [previewPvUci, engineOn, analysisQuery.data],
  );

  const legalMoves = useMemo(() => movesByOrigin(currentFen), [currentFen]);
  const turnColor = currentFen.split(" ")[1] === "b" ? "black" : "white";

  /** Juega una secuencia de jugadas desde la posición actual, dejando el
   * cursor al final. Con una sola jugada es el caso de arrastrar una pieza;
   * con varias, el de pulsar una jugada del panel del motor. */
  const playLine = useCallback(
    (sanMoves: string[]) => {
      if (!tree) return;
      let updatedTree = tree;
      let cursorId = currentId;
      let addedSomething = false;
      for (const san of sanMoves) {
        const result = addMove(updatedTree, cursorId, san);
        if (!result) break; // jugada ilegal: se para donde llegó
        updatedTree = result.root;
        cursorId = result.nodeId;
        addedSomething ||= !result.existed;
      }
      setTree(updatedTree);
      setCurrentId(cursorId);
      if (addedSomething) scheduleSave(updatedTree);
    },
    [tree, currentId, scheduleSave],
  );

  const handleBoardMove = useCallback(
    (from: string, to: string) => {
      if (!currentFen) return;
      const chess = new Chess(currentFen);
      try {
        // La promoción siempre a dama: elegir pieza es un extra que no aporta
        // en un tablero de análisis y complicaría el flujo de arrastre.
        const move = chess.move({ from, to, promotion: "q" });
        playLine([move.san]);
      } catch {
        // movimiento ilegal (chessground ya filtra casi todos)
      }
    },
    [currentFen, playLine],
  );

  function mutateTree(transform: (current: TreeNode) => TreeNode, fallbackId?: string) {
    if (!tree) return;
    const updated = transform(tree);
    setTree(updated);
    if (fallbackId && !findNode(updated, currentId)) setCurrentId(fallbackId);
    scheduleSave(updated);
  }

  // Navegación por la línea actual: lo que queda detrás del cursor y lo que
  // queda delante. Los dos caminos van en `useMemo` porque de ellos cuelgan
  // los saltos de abajo y, a través de ellos, el listener de teclado:
  // recalcularlos en cada render volvería a registrarlo continuamente.
  const pathToCurrent = useMemo(
    () => (tree ? pathToNode(tree, currentId) : []),
    [tree, currentId],
  );
  const lineAhead = useMemo(() => (currentNode ? mainLine(currentNode) : []), [currentNode]);
  const movesBehind = Math.max(0, pathToCurrent.length - 1);

  const goToStart = useCallback(() => tree && setCurrentId(tree.id), [tree]);
  const goToPrevious = useCallback(() => {
    if (pathToCurrent.length > 1) setCurrentId(pathToCurrent[pathToCurrent.length - 2].id);
  }, [pathToCurrent]);
  const goToNext = useCallback(() => {
    const nextNode = currentNode?.children[0];
    if (nextNode) setCurrentId(nextNode.id);
  }, [currentNode]);
  const goToEnd = useCallback(() => {
    const lastNode = lineAhead[lineAhead.length - 1];
    if (lastNode) setCurrentId(lastNode.id);
  }, [lineAhead]);

  useMoveNavigationKeys({
    onFirst: goToStart,
    onPrevious: goToPrevious,
    onNext: goToNext,
    onLast: goToEnd,
  });

  if (boardQuery.isPending) return <Spinner label="Cargando el tablero…" />;
  if (boardQuery.isError) return <ErrorBox error={boardQuery.error} onRetry={boardQuery.refetch} />;
  if (!tree || !currentNode) return <Spinner />;

  const board = boardQuery.data;
  const lastMoveUci = currentNode.uci;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/boards" className="text-sm opacity-70 hover:underline">
            ← Volver a tableros
          </Link>
          <h1 className="mt-1 text-2xl font-bold">{board.title}</h1>
          <p className="text-sm opacity-60">
            {saveState === "saving" && "Guardando…"}
            {saveState === "saved" && "Guardado"}
            {saveState === "error" && "No se pudo guardar"}
            {saveState === "idle" && "Todo guardado"}
          </p>
          {/* Es una propiedad del tablero, no una acción sobre él: vive con el
              título y deja la barra de acciones con el mismo orden que el
              visor. */}
          <label className="mt-1 flex items-center gap-1.5 text-sm">
            <input
              type="checkbox"
              checked={board.is_own_game}
              disabled={ownGameMutation.isPending}
              onChange={(event) => ownGameMutation.mutate(event.target.checked)}
            />
            Partida propia
            {ownGameMutation.isPending && <span className="opacity-60">guardando…</span>}
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Mismo nombre y misma posición que en el visor. */}
          <Button onClick={() => setOrientation(orientation === "white" ? "black" : "white")}>
            Girar tablero
          </Button>
          <EngineSelect value={engine} onChange={setEngine} />
          <Button onClick={() => setEngineOn(!engineOn)}>
            {engineOn ? "Apagar motor" : "Encender motor"}
          </Button>
          <Button
            variant="primary"
            onClick={() => copyPgnMutation.mutate(toPgn(tree))}
            title="Copia el árbol completo, con variantes, al portapapeles"
          >
            Copiar PGN
          </Button>
        </div>
      </div>

      {saveMutation.isError && <ErrorBox error={saveMutation.error} />}
      {ownGameMutation.isError && <ErrorBox error={ownGameMutation.error} />}
      {copyPgnMutation.isError && <ErrorBox error={copyPgnMutation.error} />}
      {copyPgnMutation.isSuccess && <SuccessBox>PGN copiado al portapapeles.</SuccessBox>}

      <div className={BOARD_SIDEBAR_GRID_CLASS}>
        <div className="space-y-3">
          <BoardWithEvalBar
            fen={currentFen}
            orientation={orientation}
            engineArrows={engineArrows}
            lastMoveUci={lastMoveUci}
            legalMoves={legalMoves}
            turnColor={turnColor}
            onMove={handleBoardMove}
            whiteWinPercent={
              engineOn && bestLine && !isEvaluationStale
                ? whiteWinPercentFromScore(bestLine)
                : null
            }
          />

          <MoveNavigator
            onFirst={goToStart}
            onPrevious={goToPrevious}
            onNext={goToNext}
            onLast={goToEnd}
            canGoBack={movesBehind > 0}
            canGoForward={lineAhead.length > 0}
            position={`${movesBehind} / ${movesBehind + lineAhead.length}`}
          />

          <p className={BOARD_HINT_CLASSES}>
            Arrastra una pieza para añadir la jugada. ← → recorren la línea, Inicio y Fin van a
            sus extremos. Señala una jugada del panel del motor para verla sobre el tablero.
          </p>
        </div>

        <aside className="space-y-3">
          <EngineLines
            lines={analysisQuery.data}
            engineName={engine}
            isEngineOn={engineOn}
            isLoading={analysisQuery.isFetching || isEvaluationStale}
            error={analysisQuery.isError ? analysisQuery.error : null}
            onPlayLine={playLine}
            onPreviewLine={setPreviewPvUci}
          />

          <Panel title="Variantes" bodyClassName="">
            <VariationTree
              root={tree}
              currentId={currentId}
              onSelect={setCurrentId}
              onPromote={(nodeId) => mutateTree((current) => promoteNode(current, nodeId))}
              onDelete={(nodeId) => {
                const move = findNode(tree, nodeId)?.san ?? "esta jugada";
                if (window.confirm(`¿Eliminar ${move} y todo lo que sigue? No se puede deshacer.`)) {
                  mutateTree((current) => deleteNode(current, nodeId), tree.id);
                }
              }}
            />
          </Panel>
        </aside>
      </div>
    </div>
  );
}

/** Jugadas legales agrupadas por casilla de origen, en el formato que espera
 * chessground para permitir el arrastre. */
function movesByOrigin(fen: string): Map<string, string[]> {
  const destsByOrigin = new Map<string, string[]>();
  if (!fen) return destsByOrigin;
  try {
    const chess = new Chess(fen);
    for (const move of chess.moves({ verbose: true })) {
      destsByOrigin.set(move.from, [...(destsByOrigin.get(move.from) ?? []), move.to]);
    }
  } catch {
    // FEN inválido: sin jugadas, el tablero queda en modo lectura
  }
  return destsByOrigin;
}

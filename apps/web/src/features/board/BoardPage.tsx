/** Tablero de análisis (RF-6.2 a RF-6.9): mover piezas, ramificar variantes,
 * ver lo que dice el motor en vivo, autoguardar con deshacer y rehacer,
 * sacar o traer el árbol completo como PGN, y pedir el análisis completo de
 * la línea principal.
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
import type { BoardDetail } from "@lucia/shared-types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/Button";
import { EngineSelect } from "../../components/EngineSelect";
import { FieldLabel } from "../../components/FieldLabel";
import { KEYBOARD_MOVE_HINT, OCCUPANCY_TOGGLE_KEY_HINT } from "../../components/board/hints";
import { BoardWithEvalBar } from "../../components/board/BoardWithEvalBar";
import { MoveNavigator } from "../../components/board/MoveNavigator";
import { useMoveNavigationKeys } from "../../components/board/useMoveNavigationKeys";
import { arrowsFromEngineLines, arrowsFromPreviewLine } from "../../components/board/boardConfig";
import { legalMovesByOrigin } from "../../components/board/legalMoves";
import { OccupancyPanel } from "../../components/board/OccupancyPanel";
import { useOccupancy } from "../../components/board/useOccupancy";
import { ErrorBox, ProgressBox, Spinner, SuccessBox, WarningBox } from "../../components/Feedback";
import { Panel } from "../../components/Panel";
import {
  BOARD_HINT_CLASSES,
  BOARD_SIDEBAR_GRID_CLASS,
  FIELD_CLASSES,
} from "../../components/styles";
import { api } from "../../lib/api";
import {
  formatAccuracy,
  formatBoardTitleFromPgnHeaders,
  formatDuration,
  formatEngineName,
  type EngineId,
} from "../../lib/format";
import { tryMove } from "../../lib/moves";
import { whiteWinPercentFromScore } from "../../lib/score";
import { EngineLines } from "./EngineLines";
import { VariationTree } from "./VariationTree";
import { OwnGamePanel, OwnGameStatus } from "./OwnGamePanel";
import { useUndoRedoKeys } from "./useUndoRedoKeys";
import { useElapsedSeconds, useTrackedAnalysis } from "../../lib/useTrackedAnalysis";
import {
  addMove,
  createRoot,
  deleteNode,
  findNode,
  isTreeNode,
  mainLine,
  matchAnalyzedLine,
  pathToNode,
  promoteNode,
  toPgn,
  fromPgn,
  type TreeNode,
} from "./tree";

/** Espera antes de guardar y antes de pedir análisis. Sin esto, cada jugada
 * en una secuencia rápida lanzaría su propia petición. */
const AUTOSAVE_DELAY_MS = 800;
const ANALYSIS_DELAY_MS = 400;

export function BoardPage() {
  const { boardId } = useParams({ from: "/boards/$boardId" });
  const id = Number(boardId);

  const queryClient = useQueryClient();
  const boardQuery = useQuery({
    queryKey: ["board", id],
    queryFn: () => api.getBoard(id),
  });

  /** Lo que devuelve cada escritura es el tablero entero —con `can_undo` y
   * `can_redo` al día—, así que se guarda en la caché en vez de pedirlo otra
   * vez: la pantalla lee el historial de ahí y no de un estado paralelo. */
  const cacheBoard = useCallback(
    (board: BoardDetail) => queryClient.setQueryData(["board", id], board),
    [queryClient, id],
  );

  const [tree, setTree] = useState<TreeNode | null>(null);
  const [currentId, setCurrentId] = useState("root");
  const [orientation, setOrientation] = useState<"white" | "black">("white");
  const [engine, setEngine] = useState<EngineId>("stockfish");
  const [engineOn, setEngineOn] = useState(true);
  const [previewPvUci, setPreviewPvUci] = useState<string[] | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  // Carga inicial del árbol guardado.
  useEffect(() => {
    if (!boardQuery.data || tree) return;
    setTree(treeFromBoard(boardQuery.data));
  }, [boardQuery.data, tree]);

  // El PGN viaja con cada guardado: si el tablero está publicado como partida
  // propia (RF-6.5), es lo que mantiene al día su fila del historial, y la API
  // lo rechaza sin él. Se manda siempre en vez de mirar antes si el tablero
  // está publicado, que dejaría el guardado dependiendo de una caché.
  const saveMutation = useMutation({
    mutationFn: (updated: TreeNode) =>
      api.updateBoard(id, { tree_json: updated, pgn: toPgn(updated) }),
    onSuccess: (board) => {
      setSaveState("saved");
      cacheBoard(board);
    },
    // Sin esto la cabecera se quedaba en "Guardando…" para siempre mientras
    // un recuadro de error decía lo contrario dos líneas más abajo.
    onError: () => setSaveState("error"),
  });

  // Marcar el tablero como partida propia (RF-6.5) pide cuatro datos que el
  // tablero no tiene, así que es un formulario y no una casilla; lo lleva
  // `OwnGamePanel`.
  const [isEditingOwnGame, setIsEditingOwnGame] = useState(false);

  const copyPgnMutation = useMutation({
    mutationFn: (pgn: string) => navigator.clipboard.writeText(pgn),
  });

  // --- Importar PGN (RF-6.7) ---
  // El PGN pegado **sustituye** el árbol, no se mezcla con él: "importar el
  // tablero completo" es traer otra partida, y fundir dos árboles daría un
  // tercero que no es ninguno de los dos. Por eso se avisa cuando hay
  // jugadas que perder.
  const [pgnToImport, setPgnToImport] = useState<string | null>(null);
  const importPgnMutation = useMutation({
    mutationFn: async (pgn: string) => {
      // `fromPgn` lanza con el motivo concreto ("no hay jugadas" o "el FEN de
      // la cabecera es ilegal"), que es lo que acaba en el `ErrorBox`.
      const parsed = fromPgn(pgn);
      // El título va con las jugadas: importar sustituye la partida entera, y
      // un tablero llamado "Siciliana" que ahora contiene otra cosa no se
      // podría renombrar desde ninguna pantalla.
      const title = formatBoardTitleFromPgnHeaders(parsed.headers) ?? undefined;
      await api.updateBoard(id, {
        title,
        root_fen: parsed.root.fen,
        tree_json: parsed.root,
        pgn: toPgn(parsed.root),
      });
      return parsed;
    },
    onSuccess: (parsed) => {
      setTree(parsed.root);
      setCurrentId(parsed.root.id);
      setPgnToImport(null);
      setSaveState("saved");
      void boardQuery.refetch(); // el título y el `root_fen` pudieron cambiar
    },
  });

  // Autoguardado con retardo (RF-6.4): el historial que se construye
  // encima es RF-6.8, y lo lleva el servidor.
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingTree = useRef<TreeNode | null>(null);
  const scheduleSave = useCallback(
    (updated: TreeNode) => {
      setSaveState("saving");
      pendingTree.current = updated;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => {
        pendingTree.current = null;
        saveMutation.mutate(updated);
      }, AUTOSAVE_DELAY_MS);
    },
    [saveMutation],
  );
  useEffect(() => () => void (saveTimer.current && clearTimeout(saveTimer.current)), []);

  /** Guarda ya lo que estuviera esperando al retardo.
   *
   * Deshacer justo después de mover llegaría antes que el autoguardado y
   * retiraría la jugada **anterior**, dejando la recién hecha encima: el
   * historial tiene que estar al día antes de moverse por él. */
  const flushPendingSave = useCallback(async () => {
    if (!pendingTree.current) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    const waiting = pendingTree.current;
    pendingTree.current = null;
    await saveMutation.mutateAsync(waiting);
  }, [saveMutation]);

  // --- Deshacer y rehacer (RF-6.8) ---
  // El árbol que vuelve es el que guardó el servidor; el cursor se lleva a la
  // raíz si la jugada donde estaba ya no existe en él.
  const historyMutation = useMutation({
    // Un tablero publicado como partida propia (RF-6.5) no necesita nada de
    // aquí: cada versión del historial guarda su PGN, así que el servidor pone
    // al día la partida en esta misma petición.
    mutationFn: async (direction: "undo" | "redo") => {
      await flushPendingSave();
      return direction === "undo" ? api.undoBoard(id) : api.redoBoard(id);
    },
    onSuccess: (board) => {
      const restored = treeFromBoard(board);
      setTree(restored);
      setCurrentId((previous) => (findNode(restored, previous) ? previous : restored.id));
      setSaveState("saved");
      cacheBoard(board);
    },
  });
  const undoBoard = useCallback(() => historyMutation.mutate("undo"), [historyMutation]);
  const redoBoard = useCallback(() => historyMutation.mutate("redo"), [historyMutation]);
  useUndoRedoKeys({ onUndo: undoBoard, onRedo: redoBoard });

  // --- Análisis completo de la línea principal (RF-6.9) ---
  // Es el mismo trabajo de motor que el de una partida y va por el mismo
  // worker; lo propio de aquí es que el PGN se manda desde el front, porque
  // quien sabe recorrer el árbol es chess.js.
  const [boardAnalysisId, setBoardAnalysisId] = useState<number | null>(null);
  const boardAnalysesQuery = useQuery({
    queryKey: ["analyses", "board", id],
    queryFn: () => api.listAnalyses({ boardId: id }),
  });
  useEffect(() => {
    const latest = boardAnalysesQuery.data?.[0];
    if (boardAnalysisId === null && latest) setBoardAnalysisId(latest.id);
  }, [boardAnalysesQuery.data, boardAnalysisId]);

  const {
    analysis: boardAnalysis,
    isRunning: isAnalysisRunning,
    progress: analysisProgress,
  } = useTrackedAnalysis(boardAnalysisId);
  // El reloj acompaña a la barra en las dos pantallas: con posiciones ya
  // cacheadas la barra avanza a saltos, y solo el reloj dice cuánto se lleva
  // esperado de verdad.
  const elapsedSeconds = useElapsedSeconds(isAnalysisRunning);

  const analyzeBoardMutation = useMutation({
    mutationFn: async () => {
      await flushPendingSave(); // se analiza lo guardado, no lo que iba a guardarse
      return api.analyzeBoard(id, { pgn: toPgn(tree as TreeNode), engine });
    },
    // Seguir el recién encolado: la lista solo hace falta al entrar, para
    // encontrar el análisis que ya hubiera.
    onSuccess: (created) => setBoardAnalysisId(created.id),
  });

  const mainLineMoves = useMemo(() => (tree ? mainLine(tree) : []), [tree]);
  const currentNode = tree ? (findNode(tree, currentId) ?? tree) : null;
  const currentFen = currentNode?.fen ?? "";

  // El análisis se pide con retardo para no lanzar una petición por cada
  // jugada mientras se avanza rápido por una línea.
  const [positionFen, setPositionFen] = useState("");
  useEffect(() => {
    if (!engineOn || !currentFen) return;
    const timer = setTimeout(() => setPositionFen(currentFen), ANALYSIS_DELAY_MS);
    return () => clearTimeout(timer);
  }, [currentFen, engineOn]);

  // Mientras el retardo no ha vencido, lo que hay en pantalla es la evaluación
  // de la posición anterior. Callarlo hace que la barra contradiga al tablero
  // durante una secuencia rápida de jugadas (criterio C-3).
  const isEvaluationStale = engineOn && currentFen !== "" && positionFen !== currentFen;

  const positionAnalysisQuery = useQuery({
    queryKey: ["position", positionFen, engine],
    queryFn: () => api.analyzePosition({ fen: positionFen, engine }),
    enabled: engineOn && positionFen !== "",
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
  const bestLine = positionAnalysisQuery.data?.[0];
  const engineArrows = useMemo(
    () =>
      previewPvUci
        ? arrowsFromPreviewLine(previewPvUci)
        : engineOn
          ? arrowsFromEngineLines(positionAnalysisQuery.data)
          : [],
    [previewPvUci, engineOn, positionAnalysisQuery.data],
  );

  const analyzedLine = useMemo(
    () =>
      matchAnalyzedLine(mainLineMoves, boardAnalysis?.status === "done" ? boardAnalysis.moves : []),
    [mainLineMoves, boardAnalysis],
  );

  // La capa de ocupación (RF-7) se calcula sobre la posición del nodo actual,
  // igual que en el visor de partidas.
  const occupancyController = useOccupancy(currentFen);

  const legalMoves = useMemo(() => legalMovesByOrigin(currentFen), [currentFen]);
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
      const move = tryMove(currentFen, from, to);
      if (move) playLine([move.san]);
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
  const pathToCurrent = useMemo(() => (tree ? pathToNode(tree, currentId) : []), [tree, currentId]);
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
  if (!tree || !currentNode) return <Spinner label="Cargando el tablero…" />;

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
          <OwnGameStatus
            ownGame={board.own_game ?? null}
            isEditing={isEditingOwnGame}
            onToggleEditing={() => setIsEditingOwnGame(!isEditingOwnGame)}
          />
        </div>

        {/* Orden acordado con el visor: girar · historial · motor · las
            acciones que sacan el árbol de aquí · la principal. Son ocho
            controles y sin un orden fijo cambiar de pantalla obligaba a
            buscarlos (criterio C-2 de docs/07-coherencia-ui.md). */}
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => setOrientation(orientation === "white" ? "black" : "white")}>
            Girar tablero
          </Button>
          {/* Los dos van juntos y en este orden, como en cualquier editor.
              Deshabilitados en vez de escondidos cuando no hay historial:
              así se ve que la función existe y por qué no se puede usar
              ahora (criterio C-3). Los atajos se anuncian en la línea de
              ayuda de debajo del tablero, que es donde esta pantalla y el
              visor anuncian los suyos. */}
          <Button onClick={undoBoard} disabled={!board.can_undo || historyMutation.isPending}>
            {/* Mientras la petición viaja, el botón lo dice, como "Eliminando…"
                en Tableros o "Abriendo…" en el visor: sin esto la única señal
                era que los dos botones se apagaran (criterio C-3). */}
            {historyMutation.isPending && historyMutation.variables === "undo"
              ? "Deshaciendo…"
              : "Deshacer"}
          </Button>
          <Button onClick={redoBoard} disabled={!board.can_redo || historyMutation.isPending}>
            {historyMutation.isPending && historyMutation.variables === "redo"
              ? "Rehaciendo…"
              : "Rehacer"}
          </Button>
          <EngineSelect value={engine} onChange={setEngine} />
          <Button onClick={() => setEngineOn(!engineOn)}>
            {engineOn ? "Apagar motor" : "Encender motor"}
          </Button>
          {/* Junto a "Copiar PGN": son la misma operación en los dos
              sentidos. Secundario frente a ella porque traer otra partida
              descarta lo que hay. */}
          <Button
            onClick={() => {
              // Abrir el panel limpia el desenlace de la importación
              // anterior: un recuadro verde de hace dos minutos junto a un
              // campo vacío se lee como si lo recién pegado ya estuviera
              // dentro (criterio C-3).
              importPgnMutation.reset();
              setPgnToImport(pgnToImport === null ? "" : null);
            }}
          >
            {pgnToImport === null ? "Importar PGN" : "Cancelar"}
          </Button>
          <Button onClick={() => copyPgnMutation.mutate(toPgn(tree))}>Copiar PGN</Button>
          {/* La acción principal de la pantalla pasa a ser esta, como en el
              visor: es la que cuesta minutos de motor y la que se viene a
              hacer. Solo se analiza la línea principal; las variantes se
              exploran con el motor en vivo, que es para lo que está. */}
          <Button
            variant="primary"
            onClick={() => analyzeBoardMutation.mutate()}
            disabled={
              mainLineMoves.length === 0 || analyzeBoardMutation.isPending || isAnalysisRunning
            }
          >
            {/* "Reanalizar" solo si lo terminado es de **este** motor, como
                en el visor: con el análisis hecho con Stockfish y Lc0 elegido
                en el desplegable, "Reanalizar con Lc0" prometía repetir algo
                que nunca se hizo (criterio C-2). */}
            {isAnalysisRunning || analyzeBoardMutation.isPending
              ? "Analizando…"
              : boardAnalysis?.status === "done" && boardAnalysis.engine === engine
                ? `Reanalizar con ${formatEngineName(engine)}`
                : `Analizar con ${formatEngineName(engine)}`}
          </Button>
        </div>
      </div>

      {/* Qué hacen las acciones de la cabecera, a la vista y no en un `title`:
          con teclado un `title` no aparece nunca, y en un botón deshabilitado
          —que es como están "Deshacer" y "Rehacer" sin historial— tampoco. Es
          la misma línea con la que el visor explica las suyas (fila 103 del
          inventario de docs/07-coherencia-ui.md, criterios C-6 y C-7). Los
          atajos de deshacer y rehacer no se repiten aquí: van en la frase bajo
          el tablero, que es donde las dos pantallas anuncian los suyos. */}
      <p className="text-xs opacity-60">
        <strong className="font-medium">Deshacer</strong> y{" "}
        <strong className="font-medium">Rehacer</strong> recorren los cambios del árbol, jugada a
        jugada. <strong className="font-medium">Importar PGN</strong> trae una partida con sus
        variantes y comentarios desde lichess, ChessBase o SCID, y descarta lo que haya aquí.{" "}
        <strong className="font-medium">Copiar PGN</strong> copia el árbol completo, con variantes,
        al portapapeles. <strong className="font-medium">Analizar</strong> clasifica las jugadas de
        la línea principal con {formatEngineName(engine)}, como en una partida.
      </p>

      {isEditingOwnGame && tree && (
        <OwnGamePanel
          boardId={id}
          ownGame={board.own_game ?? null}
          pgn={toPgn(tree)}
          hasMoves={mainLineMoves.length > 0}
          onSaved={(saved) => {
            cacheBoard(saved);
            setIsEditingOwnGame(false);
          }}
        />
      )}

      {pgnToImport !== null && (
        <Panel>
          <FieldLabel label="PGN a importar">
            <textarea
              value={pgnToImport}
              onChange={(event) => setPgnToImport(event.target.value)}
              rows={6}
              placeholder={'[Event "..."]\n\n1. e4 e5 (1... c5 {Siciliana}) 2. Nf3 *'}
              className={`w-full font-mono text-xs ${FIELD_CLASSES}`}
            />
          </FieldLabel>
          {/* El aviso va antes de pulsar, no después, en `WarningBox` y no
              en una línea gris de `text-xs`: cambia lo que va a pasar al
              pulsar el botón de al lado, que es justo lo que el criterio C-3
              llama letra pequeña. Desde RF-6.8 la importación se deshace, y
              el aviso lo dice en vez de asustar de más. */}
          {mainLineMoves.length > 0 && (
            <div className="mt-2">
              <WarningBox>
                Importar sustituye lo que hay en este tablero: {mainLineMoves.length} jugadas de la
                línea principal y sus variantes. Se puede deshacer con «Deshacer» o Ctrl+Z.
              </WarningBox>
            </div>
          )}
          <div className="mt-2">
            {/* Secundaria: la acción principal de la pantalla es "Copiar PGN"
                y solo hay una por pantalla (components/Button.tsx), la misma
                regla por la que "Importar" es secundario en Partidas. */}
            <Button
              onClick={() => importPgnMutation.mutate(pgnToImport)}
              disabled={pgnToImport.trim() === "" || importPgnMutation.isPending}
            >
              {importPgnMutation.isPending ? "Importando…" : "Importar"}
            </Button>
          </div>
        </Panel>
      )}

      {/* --- Estado del análisis del tablero (RF-6.9) --- */}
      {isAnalysisRunning && boardAnalysis && (
        <ProgressBox
          label={`Analizando la línea principal con ${formatEngineName(boardAnalysis.engine)}…`}
          detail={
            // "posición", como en el visor: es el mismo contador del mismo
            // trabajo y contarlo con dos palabras distintas en dos pantallas
            // lo hace parecer dos cosas (criterio C-5).
            <>
              {analysisProgress
                ? `posición ${analysisProgress.ply} de ${analysisProgress.total}`
                : "en cola"}{" "}
              · {formatDuration(elapsedSeconds)}
            </>
          }
          progress={
            analysisProgress && analysisProgress.total > 0
              ? (analysisProgress.ply / analysisProgress.total) * 100
              : null
          }
        />
      )}
      {/* Un análisis que falló es un error, no un aviso: el mismo estado se
          enseña con `ErrorBox` en el visor y tiene que verse igual en los dos
          sitios (criterios C-2 y C-4). */}
      {boardAnalysis?.status === "error" && (
        <ErrorBox error={new Error(boardAnalysis.error ?? "el análisis falló")} />
      )}
      {/* Sin análisis no hay insignias de clasificación en el árbol, y sin
          decirlo aparecerían de la nada la primera vez. El visor lo resuelve
          igual con su `EmptyState` de "Sin analizar" (criterio C-3). */}
      {boardAnalysis === undefined && !isAnalysisRunning && mainLineMoves.length > 0 && (
        <p className="text-xs opacity-60">
          Esta línea principal no está analizada: las jugadas salen sin clasificar hasta que pulses
          «Analizar».
        </p>
      )}
      {/* El tablero se sigue editando después de analizarlo, así que hay que
          decir cuándo lo que se ve ya no es lo que se analizó: callarlo
          dejaría clasificaciones de otra partida sobre estas jugadas. */}
      {analyzedLine.hasChangedSinceAnalysis && (
        <WarningBox>
          La línea principal cambió desde el último análisis: las jugadas que ya no coinciden salen
          sin clasificar. Vuelve a analizar para ponerlo al día.
        </WarningBox>
      )}
      {!analyzedLine.hasChangedSinceAnalysis && analyzedLine.movesAddedSinceAnalysis > 0 && (
        <WarningBox>
          {analyzedLine.movesAddedSinceAnalysis === 1
            ? "Hay 1 jugada nueva"
            : `Hay ${analyzedLine.movesAddedSinceAnalysis} jugadas nuevas`}{" "}
          desde el último análisis, aún sin clasificar.
        </WarningBox>
      )}

      {/* El motivo de un control deshabilitado se enseña, no se esconde en un
          `title` que con teclado no aparece: es la regla que cerró la fila 56
          en la barra de filtros de Partidas (criterio C-3). */}
      {mainLineMoves.length === 0 && (
        <p className="text-xs opacity-60">
          «Analizar» se activa en cuanto la línea principal tenga alguna jugada.
        </p>
      )}
      {analyzeBoardMutation.isError && <ErrorBox error={analyzeBoardMutation.error} />}
      {/* Si la consulta de los análisis anteriores falla, callarlo deja la
          pantalla como si el tablero no se hubiera analizado nunca. El visor
          ya lo dice con la suya (criterio C-3). */}
      {boardAnalysesQuery.isError && (
        <ErrorBox error={boardAnalysesQuery.error} onRetry={boardAnalysesQuery.refetch} />
      )}
      {historyMutation.isError && <ErrorBox error={historyMutation.error} />}
      {importPgnMutation.isError && <ErrorBox error={importPgnMutation.error} />}
      {/* Importar termina igual que copiar: diciendo qué pasó y con cuánto,
          como el recuadro verde de la importación de Partidas. Sin esto, el
          único desenlace era que el tablero cambiara solo (criterio C-3). */}
      {importPgnMutation.isSuccess && (
        <SuccessBox>
          PGN importado: {mainLine(importPgnMutation.data.root).length} jugadas en la línea
          principal.
          {/* Una importación a medias no puede anunciarse como completa: si
              alguna rama no encajaba, se dice aquí y no se descubre al
              recorrer el árbol (criterio C-3). */}
          {importPgnMutation.data.truncatedBranches > 0 &&
            ` Se cortaron ${importPgnMutation.data.truncatedBranches} ramas en jugadas que no encajan en su posición.`}
        </SuccessBox>
      )}
      {saveMutation.isError && <ErrorBox error={saveMutation.error} />}
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
            occupancyController={occupancyController}
            whiteWinPercent={
              engineOn && bestLine && !isEvaluationStale ? whiteWinPercentFromScore(bestLine) : null
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

          {/* Los atajos se anuncian aquí, en la misma frase y con la misma
              forma que en el visor: un atajo que solo vive en el `title` de
              un botón no aparece nunca con teclado (criterio C-1 de
              docs/07-coherencia-ui.md, la misma razón que cerró la fila 56
              del inventario). */}
          <p className={BOARD_HINT_CLASSES}>
            Arrastra una pieza para añadir la jugada. ← → recorren la línea, Inicio y Fin van a sus
            extremos. Ctrl+Z deshace y Ctrl+Y (o Ctrl+Mayús+Z) rehace. Señala una jugada del panel
            del motor para verla sobre el tablero. {OCCUPANCY_TOGGLE_KEY_HINT} {KEYBOARD_MOVE_HINT}
          </p>

          <OccupancyPanel controller={occupancyController} />
        </div>

        <aside className="space-y-3">
          {/* En el mismo sitio y con la misma forma que en el visor: mismo
              dato, mismo panel, primero del lateral (criterios C-2 y C-5).
              Los bandos van por color y no por nombre porque un tablero de
              análisis no tiene jugadores. */}
          {boardAnalysis?.status === "done" && (
            <Panel title="Precisión" bodyClassName="p-3 text-sm">
              <div className="flex justify-between">
                <span>Blancas</span>
                <span className="tabular-nums">{formatAccuracy(boardAnalysis.white_accuracy)}</span>
              </div>
              <div className="flex justify-between">
                <span>Negras</span>
                <span className="tabular-nums">{formatAccuracy(boardAnalysis.black_accuracy)}</span>
              </div>
              <p className="mt-2 text-xs opacity-60">
                {formatEngineName(boardAnalysis.engine)} · profundidad {boardAnalysis.depth} ·{" "}
                {boardAnalysis.multipv} líneas por posición (MultiPV). Solo la línea principal.{" "}
                {/* Desde RF-6.5 la respuesta depende del tablero: publicado
                    como partida propia, su análisis entra en el dashboard
                    mientras siga siendo el de la línea principal
                    (services/own_games.py::link_analyses_to_own_game). Decir
                    siempre que no cuenta era contradecir al sistema
                    (criterio C-3). */}
                {board.own_game
                  ? "Cuenta en tus Estadísticas, como el de cualquier partida, mientras la línea principal no cambie."
                  : "No cuenta en tus Estadísticas: este tablero no está marcado como partida propia."}
              </p>
            </Panel>
          )}

          <EngineLines
            lines={positionAnalysisQuery.data}
            engineName={engine}
            isEngineOn={engineOn}
            isLoading={positionAnalysisQuery.isFetching || isEvaluationStale}
            error={positionAnalysisQuery.isError ? positionAnalysisQuery.error : null}
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
                // Ya hay deshacer (RF-6.8), así que la confirmación dice la
                // verdad: se puede volver atrás.
                if (window.confirm(`¿Eliminar ${move} y todo lo que sigue?`)) {
                  mutateTree((current) => deleteNode(current, nodeId), tree.id);
                }
              }}
              analyzedByNodeId={analyzedLine.analyzedByNodeId}
            />
          </Panel>
        </aside>
      </div>
    </div>
  );
}

/** El árbol guardado del tablero. Un `tree_json` con forma inesperada
 * (versión anterior, edición manual) no debe romper la pantalla: se empieza
 * de cero desde el FEN raíz, que sí es fiable. */
function treeFromBoard(board: BoardDetail): TreeNode {
  return isTreeNode(board.tree_json) ? board.tree_json : createRoot(board.root_fen);
}

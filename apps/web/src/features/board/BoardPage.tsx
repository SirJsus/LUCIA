/** Tablero de análisis (RF-6.2 a RF-6.5): mover piezas, ramificar variantes,
 * ver lo que dice el motor en vivo y autoguardar. */
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ErrorBox, Spinner } from "../../components/Feedback";
import { api } from "../../lib/api";
import { Chessboard } from "../viewer/Chessboard";
import { EngineLines } from "./EngineLines";
import { VariationTree } from "./VariationTree";
import {
  addMove,
  createRoot,
  deleteNode,
  findNode,
  isTreeNode,
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
  const [engineOn, setEngineOn] = useState(true);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");

  // Carga inicial del árbol guardado. Un `tree_json` con forma inesperada
  // (versión anterior, edición manual) no debe romper la pantalla: se empieza
  // de cero desde el FEN raíz, que sí es fiable.
  useEffect(() => {
    if (!boardQuery.data || tree) return;
    const guardado = boardQuery.data.tree_json;
    setTree(isTreeNode(guardado) ? guardado : createRoot(boardQuery.data.root_fen));
  }, [boardQuery.data, tree]);

  const saveMutation = useMutation({
    mutationFn: (updated: TreeNode) => api.updateBoard(id, { tree_json: updated }),
    onSuccess: () => setSaveState("saved"),
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

  const analysisQuery = useQuery({
    queryKey: ["position", analysisFen],
    queryFn: () => api.analysePosition({ fen: analysisFen }),
    enabled: engineOn && analysisFen !== "",
    staleTime: Infinity, // la evaluación de una posición no cambia sola
  });

  const legalMoves = useMemo(() => movesByOrigin(currentFen), [currentFen]);
  const turnColor = currentFen.split(" ")[1] === "b" ? "black" : "white";

  const playSan = useCallback(
    (san: string) => {
      if (!tree) return;
      const result = addMove(tree, currentId, san);
      if (!result) return; // jugada ilegal: se ignora en silencio
      setTree(result.root);
      setCurrentId(result.nodeId);
      if (!result.existed) scheduleSave(result.root);
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
        playSan(move.san);
      } catch {
        // movimiento ilegal (chessground ya filtra casi todos)
      }
    },
    [currentFen, playSan],
  );

  function mutateTree(transform: (current: TreeNode) => TreeNode, fallbackId?: string) {
    if (!tree) return;
    const updated = transform(tree);
    setTree(updated);
    if (fallbackId && !findNode(updated, currentId)) setCurrentId(fallbackId);
    scheduleSave(updated);
  }

  // Navegación con teclado por la línea actual. El camino va en `useMemo`
  // porque es dependencia del efecto de abajo: recalcularlo en cada render
  // volvería a registrar el listener continuamente.
  const camino = useMemo(() => (tree ? pathToNode(tree, currentId) : []), [tree, currentId]);
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (event.key === "ArrowLeft" && camino.length > 1) {
        event.preventDefault();
        setCurrentId(camino[camino.length - 2].id);
      }
      if (event.key === "ArrowRight") {
        const siguiente = findNode(tree ?? createRoot(""), currentId)?.children[0];
        if (siguiente) {
          event.preventDefault();
          setCurrentId(siguiente.id);
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [camino, currentId, tree]);

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
          <h1 className="mt-1 text-xl font-bold">{board.title}</h1>
          <p className="text-sm opacity-60">
            {saveState === "saving" && "Guardando…"}
            {saveState === "saved" && "Guardado"}
            {saveState === "idle" && "Sin cambios sin guardar"}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="checkbox"
              checked={board.is_own_game}
              onChange={(event) =>
                api
                  .updateBoard(id, { is_own_game: event.target.checked })
                  .then(() => boardQuery.refetch())
              }
            />
            Partida propia
          </label>
          <button
            type="button"
            onClick={() => setEngineOn(!engineOn)}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            {engineOn ? "Apagar motor" : "Encender motor"}
          </button>
          <button
            type="button"
            onClick={() => setOrientation(orientation === "white" ? "black" : "white")}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Girar
          </button>
          <button
            type="button"
            onClick={() => navigator.clipboard.writeText(toPgn(tree))}
            title="Copia el árbol completo, con variantes, al portapapeles"
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Copiar PGN
          </button>
        </div>
      </div>

      {saveMutation.isError && <ErrorBox error={saveMutation.error} />}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_24rem]">
        <div className="space-y-3">
          <div className="mx-auto w-full max-w-[34rem]">
            <Chessboard
              fen={currentFen}
              orientation={orientation}
              lastMoveUci={lastMoveUci}
              legalMoves={legalMoves}
              turnColor={turnColor}
              onMove={handleBoardMove}
            />
          </div>
          <p className="text-center text-xs opacity-60">
            Arrastra una pieza para añadir la jugada. ← y → recorren la línea actual.
          </p>
        </div>

        <aside className="space-y-3">
          {engineOn && (
            <EngineLines
              lines={analysisQuery.data}
              isLoading={analysisQuery.isFetching}
              onPlayMove={playSan}
            />
          )}

          <div className="rounded border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <p className="border-b border-slate-200 px-3 py-2 text-sm font-medium dark:border-slate-800">
              Variantes
            </p>
            <VariationTree
              root={tree}
              currentId={currentId}
              onSelect={setCurrentId}
              onPromote={(nodeId) => mutateTree((current) => promoteNode(current, nodeId))}
              onDelete={(nodeId) =>
                mutateTree((current) => deleteNode(current, nodeId), tree.id)
              }
            />
          </div>
        </aside>
      </div>
    </div>
  );
}

/** Jugadas legales agrupadas por casilla de origen, en el formato que espera
 * chessground para permitir el arrastre. */
function movesByOrigin(fen: string): Map<string, string[]> {
  const destinos = new Map<string, string[]>();
  if (!fen) return destinos;
  try {
    const chess = new Chess(fen);
    for (const move of chess.moves({ verbose: true })) {
      destinos.set(move.from, [...(destinos.get(move.from) ?? []), move.to]);
    }
  } catch {
    // FEN inválido: sin jugadas, el tablero queda en modo lectura
  }
  return destinos;
}

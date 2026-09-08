/** Lista de tableros de análisis guardados (RF-6.4), y su creación desde la
 * posición inicial, un FEN o un PGN pegado (RF-6.1). */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { Chess } from "chess.js";
import { useState } from "react";
import { Button } from "../../components/Button";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { FIELD_CLASSES, PANEL_CLASSES } from "../../components/styles";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { addMove, createRoot, type TreeNode } from "./tree";

const STARTING_FEN = new Chess().fen();

export function BoardsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [error, setError] = useState<string | null>(null);

  const boardsQuery = useQuery({ queryKey: ["boards"], queryFn: api.listBoards });

  const createMutation = useMutation({
    mutationFn: (body: { title: string; root_fen: string; tree_json: TreeNode }) =>
      api.createBoard(body),
    onSuccess: (board) => {
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      navigate({ to: "/boards/$boardId", params: { boardId: String(board.id) } });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteBoard,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["boards"] }),
  });

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const parsed = parseSource(source);
    if (!parsed) {
      setError("No se reconoce eso como FEN ni como PGN. Déjalo vacío para empezar de cero.");
      return;
    }
    createMutation.mutate({
      title: title.trim() || "Tablero sin título",
      root_fen: parsed.rootFen,
      tree_json: parsed.tree,
    });
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Tableros de análisis</h1>
      <p className="-mt-4 text-sm opacity-70">
        Para partidas presenciales, posiciones de libro o ideas sueltas. No cuentan en tus
        estadísticas.
      </p>

      <form
        onSubmit={handleCreate}
        className={`space-y-3 p-4 ${PANEL_CLASSES}`}
      >
        <div className="flex flex-wrap gap-3">
          <label className="text-sm">
            <span className="mb-1 block opacity-70">Título</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Mi partida del club"
              className={`w-64 ${FIELD_CLASSES}`}
            />
          </label>
        </div>

        <label className="block text-sm">
          <span className="mb-1 block opacity-70">
            FEN o PGN de partida (opcional; vacío = posición inicial)
          </span>
          <textarea
            value={source}
            onChange={(event) => setSource(event.target.value)}
            rows={3}
            placeholder="rnbqkbnr/pppppppp/... o 1. e4 e5 2. Nf3"
            className={`w-full font-mono text-xs ${FIELD_CLASSES}`}
          />
        </label>

        {/* El error de validación usa el mismo recuadro que el de la API:
            antes uno era un párrafo rojo suelto y el otro un `ErrorBox`, a dos
            líneas de distancia dentro del mismo formulario. */}
        {error && <ErrorBox error={new Error(error)} />}
        {createMutation.isError && <ErrorBox error={createMutation.error} />}

        <Button type="submit" variant="primary" disabled={createMutation.isPending}>
          {createMutation.isPending ? "Creando…" : "Crear tablero"}
        </Button>
      </form>

      {boardsQuery.isPending && <Spinner />}
      {boardsQuery.isError && <ErrorBox error={boardsQuery.error} onRetry={boardsQuery.refetch} />}

      {boardsQuery.data?.length === 0 && (
        <EmptyState title="Todavía no has guardado ningún tablero" />
      )}

      {boardsQuery.data && boardsQuery.data.length > 0 && (
        <ul className="space-y-2">
          {boardsQuery.data.map((board) => (
            <li
              key={board.id}
              className={`flex items-center justify-between gap-3 px-3 py-2 ${PANEL_CLASSES}`}
            >
              <Link
                to="/boards/$boardId"
                params={{ boardId: String(board.id) }}
                className="flex-1 hover:underline"
              >
                <span className="font-medium">{board.title}</span>
                {board.is_own_game && (
                  <span className="ml-2 rounded bg-sky-100 px-1.5 py-0.5 text-xs text-sky-800 dark:bg-sky-900/60 dark:text-sky-200">
                    partida propia
                  </span>
                )}
                <span className="ml-2 text-xs opacity-60">
                  actualizado {formatDate(board.updated_at)}
                </span>
              </Link>
              <Button
                variant="danger"
                size="sm"
                onClick={() => deleteMutation.mutate(board.id)}
              >
                Eliminar
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface ParsedSource {
  rootFen: string;
  tree: TreeNode;
}

/** Acepta un FEN, un PGN o nada (RF-6.1). Se intenta primero como FEN porque
 * es más específico: un PGN nunca se confunde con un FEN válido. */
function parseSource(source: string): ParsedSource | null {
  const trimmedSource = source.trim();
  if (!trimmedSource) return { rootFen: STARTING_FEN, tree: createRoot(STARTING_FEN) };

  try {
    const chess = new Chess(trimmedSource);
    return { rootFen: chess.fen(), tree: createRoot(chess.fen()) };
  } catch {
    // no era un FEN; se intenta como PGN
  }

  try {
    const chess = new Chess();
    chess.loadPgn(trimmedSource);
    const pgnMoves = chess.history({ verbose: true });
    if (pgnMoves.length === 0) return null;

    const rootFen = pgnMoves[0].before;
    let tree = createRoot(rootFen);
    let cursor = tree.id;
    for (const move of pgnMoves) {
      const result = addMove(tree, cursor, move.san);
      if (!result) break;
      tree = result.root;
      cursor = result.nodeId;
    }
    return { rootFen, tree };
  } catch {
    return null;
  }
}
